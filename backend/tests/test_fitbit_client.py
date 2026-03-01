"""Tests for the Fitbit API client."""

from datetime import date
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.integrations.fitbit.client import FitbitDataClient, FitbitOAuth2


def _make_response(status_code: int, json_data: dict, headers: dict | None = None) -> httpx.Response:
    """Create an httpx.Response with a request set so raise_for_status works."""
    resp = httpx.Response(
        status_code,
        json=json_data,
        headers=headers or {},
    )
    resp.request = httpx.Request("GET", "https://api.fitbit.com/test")
    return resp


class TestFitbitOAuth2:
    def setup_method(self):
        with patch("app.integrations.fitbit.client.settings") as mock_settings:
            mock_settings.FITBIT_CLIENT_ID = "test_client_id"
            mock_settings.FITBIT_CLIENT_SECRET = "test_secret"
            mock_settings.FITBIT_REDIRECT_URI = "http://localhost:8000/api/v1/fitbit/callback"
            self.oauth = FitbitOAuth2()

    def test_get_authorization_url(self):
        url = self.oauth.get_authorization_url("test_state_123")
        assert "test_client_id" in url
        assert "test_state_123" in url
        assert "authorize" in url
        assert "activity" in url or "heartrate" in url or "sleep" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(self):
        token_data = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "token_type": "Bearer",
            "expires_in": 28800,
            "user_id": "ABC123",
        }
        mock_response = _make_response(200, token_data)

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await self.oauth.exchange_code("auth_code_123")

        assert result["access_token"] == "new_access_token"
        assert result["refresh_token"] == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_exchange_code_raises_on_error(self):
        mock_response = _make_response(401, {"errors": [{"errorType": "invalid_grant"}]})

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)

            with pytest.raises(httpx.HTTPStatusError):
                await self.oauth.exchange_code("bad_code")

    @pytest.mark.asyncio
    async def test_refresh_tokens_success(self):
        token_data = {
            "access_token": "refreshed_access",
            "refresh_token": "refreshed_refresh",
            "token_type": "Bearer",
            "expires_in": 28800,
        }
        mock_response = _make_response(200, token_data)

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await self.oauth.refresh_tokens("old_refresh_token")

        assert result["access_token"] == "refreshed_access"


class TestFitbitDataClient:
    def setup_method(self):
        self.client = FitbitDataClient(access_token="test_token")

    @pytest.mark.asyncio
    async def test_get_sleep_with_data(self):
        sleep_data = {
            "sleep": [
                {
                    "isMainSleep": True,
                    "minutesAsleep": 420,
                    "efficiency": 88,
                    "startTime": "2026-02-27T23:00:00.000",
                    "endTime": "2026-02-28T06:30:00.000",
                    "levels": {
                        "summary": {
                            "deep": {"minutes": 80},
                            "light": {"minutes": 200},
                            "rem": {"minutes": 100},
                            "wake": {"minutes": 40},
                        }
                    },
                }
            ]
        }
        mock_response = _make_response(200, sleep_data)

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await self.client.get_sleep(date(2026, 2, 28))

        assert result is not None
        assert result["total_minutes"] == 420
        assert result["deep_minutes"] == 80
        assert result["efficiency"] == 88

    @pytest.mark.asyncio
    async def test_get_sleep_no_data(self):
        mock_response = _make_response(200, {"sleep": []})

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await self.client.get_sleep(date(2026, 2, 28))

        assert result is None

    @pytest.mark.asyncio
    async def test_get_hrv_with_data(self):
        hrv_data = {
            "hrv": [
                {
                    "value": {
                        "dailyRmssd": 45.2,
                        "deepRmssd": 52.1,
                    }
                }
            ]
        }
        mock_response = _make_response(200, hrv_data)

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await self.client.get_hrv(date(2026, 2, 28))

        assert result is not None
        assert result["rmssd"] == 45.2
        assert result["deep_rmssd"] == 52.1

    @pytest.mark.asyncio
    async def test_get_hrv_no_data(self):
        mock_response = _make_response(200, {"hrv": []})

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await self.client.get_hrv(date(2026, 2, 28))

        assert result is None

    @pytest.mark.asyncio
    async def test_get_heart_rate(self):
        hr_data = {
            "activities-heart": [
                {
                    "value": {
                        "restingHeartRate": 58,
                        "heartRateZones": [
                            {"name": "Fat Burn", "min": 86, "max": 120},
                            {"name": "Cardio", "min": 120, "max": 150},
                        ],
                    }
                }
            ]
        }
        mock_response = _make_response(200, hr_data)

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await self.client.get_heart_rate(date(2026, 2, 28))

        assert result["resting_hr"] == 58
        assert len(result["hr_zones"]) == 2

    @pytest.mark.asyncio
    async def test_get_activity(self):
        activity_data = {
            "summary": {
                "steps": 8500,
                "caloriesOut": 2200,
                "activityCalories": 800,
                "fairlyActiveMinutes": 20,
                "veryActiveMinutes": 15,
                "sedentaryMinutes": 600,
                "distances": [
                    {"activity": "total", "distance": 6.2},
                ],
            }
        }
        mock_response = _make_response(200, activity_data)

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await self.client.get_activity(date(2026, 2, 28))

        assert result["steps"] == 8500
        assert result["calories_total"] == 2200
        assert result["active_minutes"] == 35  # 20 + 15
        assert result["distance_km"] == 6.2

    @pytest.mark.asyncio
    async def test_get_profile(self):
        profile_data = {
            "user": {
                "displayName": "Test User",
                "age": 30,
                "gender": "MALE",
                "height": 175,
                "weight": 80,
                "timezone": "Asia/Kolkata",
            }
        }
        mock_response = _make_response(200, profile_data)

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await self.client.get_profile()

        assert result["display_name"] == "Test User"
        assert result["age"] == 30
        assert result["timezone"] == "Asia/Kolkata"

    @pytest.mark.asyncio
    async def test_rate_limit_raises_exception(self):
        mock_response = _make_response(
            429,
            {"errors": [{"errorType": "rate_limit"}]},
            headers={"Retry-After": "120"},
        )

        with patch("app.integrations.fitbit.client.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(Exception, match="Rate limited"):
                await self.client.get_profile()

    @pytest.mark.asyncio
    async def test_sync_daily_data_combines_all(self):
        """sync_daily_data should call all individual methods."""
        self.client.get_sleep = AsyncMock(return_value={"total_minutes": 420})
        self.client.get_hrv = AsyncMock(return_value={"rmssd": 45})
        self.client.get_heart_rate = AsyncMock(return_value={"resting_hr": 58})
        self.client.get_activity = AsyncMock(return_value={"steps": 8000})

        result = await self.client.sync_daily_data(date(2026, 2, 28))

        assert result["sleep"]["total_minutes"] == 420
        assert result["hrv"]["rmssd"] == 45
        assert result["heart_rate"]["resting_hr"] == 58
        assert result["activity"]["steps"] == 8000
        assert result["date"] == "2026-02-28"

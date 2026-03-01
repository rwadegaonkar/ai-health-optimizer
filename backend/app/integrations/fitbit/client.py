"""Fitbit Web API client — OAuth2 flow and data retrieval."""

from datetime import date, datetime, timedelta

import httpx

from app.core.config import settings


class FitbitOAuth2:
    """OAuth2 Authorization Code flow with PKCE for Fitbit."""

    AUTH_URL = "https://www.fitbit.com/oauth2/authorize"
    TOKEN_URL = "https://api.fitbit.com/oauth2/token"
    SCOPES = "activity heartrate sleep profile weight"

    def __init__(self):
        self.client_id = settings.FITBIT_CLIENT_ID
        self.client_secret = settings.FITBIT_CLIENT_SECRET
        self.redirect_uri = settings.FITBIT_REDIRECT_URI

    def get_authorization_url(self, state: str) -> str:
        return (
            f"{self.AUTH_URL}"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={self.SCOPES}"
            f"&state={state}"
        )

    async def exchange_code(self, code: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                },
                auth=(self.client_id, self.client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def refresh_tokens(self, refresh_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                },
                auth=(self.client_id, self.client_secret),
            )
            response.raise_for_status()
            return response.json()


class FitbitDataClient:
    """Fetches health data from Fitbit Web API."""

    BASE_URL = "https://api.fitbit.com"

    def __init__(self, access_token: str):
        self.access_token = access_token

    async def _request(self, endpoint: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}{endpoint}",
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=15.0,
            )
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise Exception(f"Rate limited. Retry after {retry_after}s")
            response.raise_for_status()
            return response.json()

    async def get_sleep(self, target_date: date) -> dict | None:
        data = await self._request(
            f"/1.2/user/-/sleep/date/{target_date.isoformat()}.json"
        )
        sleep_records = data.get("sleep", [])
        if not sleep_records:
            return None

        main_sleep = next(
            (s for s in sleep_records if s.get("isMainSleep", False)),
            sleep_records[0],
        )
        stages = main_sleep.get("levels", {}).get("summary", {})

        return {
            "date": target_date.isoformat(),
            "total_minutes": main_sleep.get("minutesAsleep", 0),
            "deep_minutes": stages.get("deep", {}).get("minutes", 0),
            "light_minutes": stages.get("light", {}).get("minutes", 0),
            "rem_minutes": stages.get("rem", {}).get("minutes", 0),
            "wake_minutes": stages.get("wake", {}).get("minutes", 0),
            "efficiency": main_sleep.get("efficiency", 0),
            "start_time": main_sleep.get("startTime"),
            "end_time": main_sleep.get("endTime"),
        }

    async def get_hrv(self, target_date: date) -> dict | None:
        data = await self._request(
            f"/1/user/-/hrv/date/{target_date.isoformat()}.json"
        )
        hrv_records = data.get("hrv", [])
        if not hrv_records:
            return None

        hrv = hrv_records[0].get("value", {})
        return {
            "date": target_date.isoformat(),
            "rmssd": hrv.get("dailyRmssd", 0),
            "deep_rmssd": hrv.get("deepRmssd", 0),
        }

    async def get_heart_rate(self, target_date: date) -> dict:
        data = await self._request(
            f"/1/user/-/activities/heart/date/{target_date.isoformat()}/1d.json"
        )
        hr_data = data.get("activities-heart", [{}])[0].get("value", {})
        return {
            "date": target_date.isoformat(),
            "resting_hr": hr_data.get("restingHeartRate"),
            "hr_zones": hr_data.get("heartRateZones", []),
        }

    async def get_activity(self, target_date: date) -> dict:
        data = await self._request(
            f"/1/user/-/activities/date/{target_date.isoformat()}.json"
        )
        summary = data.get("summary", {})
        return {
            "date": target_date.isoformat(),
            "steps": summary.get("steps", 0),
            "calories_total": summary.get("caloriesOut", 0),
            "calories_active": summary.get("activityCalories", 0),
            "active_minutes": (
                summary.get("fairlyActiveMinutes", 0)
                + summary.get("veryActiveMinutes", 0)
            ),
            "sedentary_minutes": summary.get("sedentaryMinutes", 0),
            "distance_km": next(
                (d.get("distance", 0) for d in summary.get("distances", []) if d.get("activity") == "total"),
                0,
            ),
        }

    async def get_profile(self) -> dict:
        data = await self._request("/1/user/-/profile.json")
        user = data.get("user", {})
        return {
            "display_name": user.get("displayName"),
            "age": user.get("age"),
            "gender": user.get("gender"),
            "height": user.get("height"),
            "weight": user.get("weight"),
            "timezone": user.get("timezone"),
        }

    async def sync_daily_data(self, target_date: date) -> dict:
        """Fetch all data types for a given date."""
        sleep = await self.get_sleep(target_date)
        hrv = await self.get_hrv(target_date)
        heart = await self.get_heart_rate(target_date)
        activity = await self.get_activity(target_date)

        return {
            "date": target_date.isoformat(),
            "sleep": sleep,
            "hrv": hrv,
            "heart_rate": heart,
            "activity": activity,
        }

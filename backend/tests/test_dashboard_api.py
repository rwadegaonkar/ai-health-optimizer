"""Tests for dashboard and insights API endpoints."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodLog
from app.models.insights import AIInsight, MacroTarget, UserGoal, WeeklySummary
from app.models.user import User
from app.models.wearable import NormalizedMetric, WearableConnection


class TestDashboardAPI:
    @pytest.mark.asyncio
    async def test_dashboard_empty_state(self, client: AsyncClient, auth_headers):
        """Dashboard should work with no data."""
        response = await client.get("/api/v1/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["today_summary"]["total_calories"] == 0
        assert data["today_summary"]["meal_count"] == 0
        assert data["current_targets"] is None
        assert data["latest_metrics"] is None
        assert data["latest_insight"] is None
        assert len(data["weekly_calories"]) == 7

    @pytest.mark.asyncio
    async def test_dashboard_with_food_data(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        """Dashboard should reflect today's food logs."""
        # Create food logs for today
        log1 = FoodLog(
            id=uuid.uuid4(),
            user_id=test_user.id,
            food_name="Eggs",
            meal_type="breakfast",
            source="text",
            calories=200,
            protein_g=14,
            carbs_g=1,
            fat_g=15,
            fiber_g=0,
        )
        log2 = FoodLog(
            id=uuid.uuid4(),
            user_id=test_user.id,
            food_name="Rice",
            meal_type="lunch",
            source="text",
            calories=350,
            protein_g=7,
            carbs_g=70,
            fat_g=1,
            fiber_g=0,
        )
        db_session.add_all([log1, log2])
        await db_session.commit()

        response = await client.get("/api/v1/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["today_summary"]["total_calories"] == 550
        assert data["today_summary"]["total_protein_g"] == 21
        assert data["today_summary"]["meal_count"] == 2

    @pytest.mark.asyncio
    async def test_dashboard_with_macro_targets(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        """Dashboard should show active macro targets."""
        target = MacroTarget(
            id=uuid.uuid4(),
            user_id=test_user.id,
            calories=2100,
            protein_g=160,
            carbs_g=200,
            fat_g=70,
            effective_from=date.today(),
            is_active=True,
        )
        db_session.add(target)
        await db_session.commit()

        response = await client.get("/api/v1/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["current_targets"] is not None
        assert data["current_targets"]["calories"] == 2100

    @pytest.mark.asyncio
    async def test_dashboard_with_wearable_metrics(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        """Dashboard should show latest wearable metrics."""
        metric = NormalizedMetric(
            user_id=test_user.id,
            date=date.today(),
            primary_source="fitbit",
            sleep_duration_min=450,
            sleep_score=82,
            hrv_rmssd=48.5,
            rhr_bpm=59,
            steps=9200,
            active_minutes=45,
            calories_burned=2300,
            recovery_score=78,
        )
        db_session.add(metric)
        await db_session.commit()

        response = await client.get("/api/v1/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["latest_metrics"] is not None
        assert data["latest_metrics"]["hrv_rmssd"] == 48.5
        assert data["latest_metrics"]["rhr_bpm"] == 59

    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/dashboard")
        assert response.status_code == 403


class TestInsightsAPI:
    @pytest.mark.asyncio
    async def test_get_daily_insight_empty(self, client: AsyncClient, auth_headers):
        response = await client.get(
            f"/api/v1/insights/daily?target_date={date.today().isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        # No insight exists — should return null
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_get_daily_insight_with_data(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        insight = AIInsight(
            id=uuid.uuid4(),
            user_id=test_user.id,
            date=date.today(),
            insight_type="daily",
            content="Great job keeping your protein high yesterday!",
        )
        db_session.add(insight)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/insights/daily?target_date={date.today().isoformat()}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "protein" in data["content"].lower()

    @pytest.mark.asyncio
    async def test_get_weekly_summaries_empty(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/insights/weekly", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_weekly_summaries_with_data(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        summary = WeeklySummary(
            id=uuid.uuid4(),
            user_id=test_user.id,
            week_start=date.today() - timedelta(days=7),
            avg_calories=2050,
            avg_protein_g=155,
            avg_carbs_g=210,
            avg_fat_g=68,
            calorie_target=2100,
            calorie_delta=-50,
            avg_sleep_min=440,
            avg_hrv=46.0,
            avg_steps=8500,
            avg_recovery=75,
            ai_summary="Solid week overall.",
        )
        db_session.add(summary)
        await db_session.commit()

        response = await client.get("/api/v1/insights/weekly", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["avg_calories"] == 2050

    @pytest.mark.asyncio
    async def test_set_macro_targets(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/insights/targets",
            headers=auth_headers,
            json={
                "calories": 2200,
                "protein_g": 170,
                "carbs_g": 220,
                "fat_g": 70,
                "effective_from": date.today().isoformat(),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["calories"] == 2200
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_set_macro_targets_deactivates_old(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        """Setting new targets should deactivate previous ones."""
        old_target = MacroTarget(
            id=uuid.uuid4(),
            user_id=test_user.id,
            calories=1800,
            protein_g=140,
            carbs_g=180,
            fat_g=60,
            effective_from=date.today() - timedelta(days=30),
            is_active=True,
        )
        db_session.add(old_target)
        await db_session.commit()

        response = await client.post(
            "/api/v1/insights/targets",
            headers=auth_headers,
            json={
                "calories": 2200,
                "protein_g": 170,
                "carbs_g": 220,
                "fat_g": 70,
                "effective_from": date.today().isoformat(),
            },
        )
        assert response.status_code == 201

        # Check current target is the new one
        current = await client.get("/api/v1/insights/targets/current", headers=auth_headers)
        assert current.json()["calories"] == 2200

    @pytest.mark.asyncio
    async def test_get_current_targets_none(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/insights/targets/current", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_create_goal(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/insights/goals",
            headers=auth_headers,
            json={
                "goal_type": "weight_loss",
                "target_value": 75.0,
                "current_value": 80.0,
                "unit": "kg",
                "start_date": date.today().isoformat(),
                "target_date": (date.today() + timedelta(days=90)).isoformat(),
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["goal_type"] == "weight_loss"
        assert data["target_value"] == 75.0
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_list_goals(self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession):
        goal = UserGoal(
            id=uuid.uuid4(),
            user_id=test_user.id,
            goal_type="daily_steps",
            target_value=10000,
            current_value=8000,
            unit="steps",
            start_date=date.today(),
            status="active",
        )
        db_session.add(goal)
        await db_session.commit()

        response = await client.get("/api/v1/insights/goals", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["goal_type"] == "daily_steps"


class TestWearablesAPI:
    @pytest.mark.asyncio
    async def test_list_connections_empty(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/wearables/connections", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_connections_with_data(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        conn = WearableConnection(
            id=uuid.uuid4(),
            user_id=test_user.id,
            provider="fitbit",
            is_active=True,
            access_token_encrypted="encrypted_token",
            refresh_token_encrypted="encrypted_refresh",
        )
        db_session.add(conn)
        await db_session.commit()

        response = await client.get("/api/v1/wearables/connections", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["provider"] == "fitbit"
        assert data[0]["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_metrics_empty(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/wearables/metrics", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_metrics_with_data(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        metric = NormalizedMetric(
            user_id=test_user.id,
            date=date.today(),
            primary_source="fitbit",
            sleep_duration_min=420,
            hrv_rmssd=45.0,
            rhr_bpm=60,
            steps=7500,
        )
        db_session.add(metric)
        await db_session.commit()

        today = date.today().isoformat()
        response = await client.get(
            f"/api/v1/wearables/metrics?start_date={today}&end_date={today}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["steps"] == 7500

    @pytest.mark.asyncio
    async def test_get_latest_metric(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        metric = NormalizedMetric(
            user_id=test_user.id,
            date=date.today(),
            primary_source="fitbit",
            recovery_score=82,
        )
        db_session.add(metric)
        await db_session.commit()

        response = await client.get("/api/v1/wearables/metrics/latest", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["recovery_score"] == 82

    @pytest.mark.asyncio
    async def test_get_latest_metric_none(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/wearables/metrics/latest", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_disconnect_wearable(
        self, client: AsyncClient, auth_headers, test_user: User, db_session: AsyncSession
    ):
        conn_id = uuid.uuid4()
        conn = WearableConnection(
            id=conn_id,
            user_id=test_user.id,
            provider="fitbit",
            is_active=True,
            access_token_encrypted="encrypted_token",
            refresh_token_encrypted="encrypted_refresh",
        )
        db_session.add(conn)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/wearables/connections/{conn_id}", headers=auth_headers
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_wearable(self, client: AsyncClient, auth_headers):
        fake_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/wearables/connections/{fake_id}", headers=auth_headers
        )
        assert response.status_code == 404


class TestUsersAPI:
    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, auth_headers, test_user: User):
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"name": "Updated Name", "weight_kg": 78, "goal_type": "maintain"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["weight_kg"] == 78
        assert data["goal_type"] == "maintain"

    @pytest.mark.asyncio
    async def test_update_profile_partial(self, client: AsyncClient, auth_headers, test_user: User):
        """Partial update should only change specified fields."""
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"age": 31},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["age"] == 31
        assert data["name"] == "Test User"  # unchanged

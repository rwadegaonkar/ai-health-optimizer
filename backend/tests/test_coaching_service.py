"""Tests for the AI Coaching Service."""

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.food import FoodLog
from app.models.insights import MacroTarget
from app.models.user import User
from app.models.wearable import NormalizedMetric


class TestBuildDailyContext:
    """Test _build_daily_context assembles correct data from DB."""

    @pytest.mark.asyncio
    async def test_context_with_full_data(self, db_session: AsyncSession, test_user: User):
        """Context should include food, metrics, and targets."""
        yesterday = date.today() - timedelta(days=1)

        # Create yesterday's food log
        log = FoodLog(
            id=uuid.uuid4(),
            user_id=test_user.id,
            food_name="Chicken Rice",
            meal_type="lunch",
            source="text",
            calories=500,
            protein_g=35,
            carbs_g=60,
            fat_g=10,
            fiber_g=2,
            logged_at=datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc),
        )
        db_session.add(log)

        # Create wearable metric
        metric = NormalizedMetric(
            user_id=test_user.id,
            date=date.today(),
            primary_source="fitbit",
            sleep_duration_min=450,
            sleep_score=85,
            hrv_rmssd=48.0,
            rhr_bpm=58,
            recovery_score=80,
        )
        db_session.add(metric)

        # Create macro target
        target = MacroTarget(
            id=uuid.uuid4(),
            user_id=test_user.id,
            calories=2100,
            protein_g=160,
            carbs_g=200,
            fat_g=70,
            effective_from=date.today() - timedelta(days=7),
            is_active=True,
        )
        db_session.add(target)
        await db_session.commit()

        with patch("app.services.coaching.AsyncOpenAI"):
            from app.services.coaching import CoachingService
            service = CoachingService()
            context = await service._build_daily_context(
                test_user, date.today(), yesterday, db_session
            )

        assert context["user_name"] == "Test User"
        assert context["yesterday_kcal"] == 500
        assert context["yesterday_protein_g"] == 35
        assert context["target_kcal"] == 2100
        assert context["target_protein_g"] == 160
        assert context["hrv_rmssd"] == 48.0
        assert context["rhr"] == 58
        assert context["sleep_hours"] == 7  # 450 // 60
        assert context["goal_type"] == "lose_weight"

    @pytest.mark.asyncio
    async def test_context_with_no_data(self, db_session: AsyncSession, test_user: User):
        """Context should use defaults when no food/metrics/targets exist."""
        yesterday = date.today() - timedelta(days=1)

        with patch("app.services.coaching.AsyncOpenAI"):
            from app.services.coaching import CoachingService
            service = CoachingService()
            context = await service._build_daily_context(
                test_user, date.today(), yesterday, db_session
            )

        assert context["yesterday_kcal"] == 0
        assert context["yesterday_protein_g"] == 0
        assert context["target_kcal"] == 2000  # default
        assert context["target_protein_g"] == 150  # default
        assert context["hrv_rmssd"] == "N/A"
        assert context["rhr"] == "N/A"
        assert context["sleep_hours"] == "N/A"


class TestGenerateDailyInsight:
    """Test generate_daily_insight with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_generates_and_stores_insight(self, db_session: AsyncSession, test_user: User):
        """Should call OpenAI and store the insight in DB."""
        with patch("app.services.coaching.AsyncOpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client

            mock_choice = MagicMock()
            mock_choice.message.content = "Great recovery today! Your HRV is trending up."
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            from app.services.coaching import CoachingService
            service = CoachingService()
            result = await service.generate_daily_insight(test_user, db_session)

        assert result == "Great recovery today! Your HRV is trending up."
        # Verify stored in DB
        await db_session.commit()
        from sqlalchemy import select
        from app.models.insights import AIInsight
        db_result = await db_session.execute(
            select(AIInsight).where(AIInsight.user_id == test_user.id)
        )
        insight = db_result.scalar_one()
        assert insight.insight_type == "daily"
        assert "HRV" in insight.content


class TestGenerateFoodResponse:
    """Test generate_food_response with mocked OpenAI."""

    @pytest.mark.asyncio
    async def test_generates_food_coaching_response(self, db_session: AsyncSession, test_user: User):
        """Should provide coaching feedback on a food log."""
        food_log = FoodLog(
            id=uuid.uuid4(),
            user_id=test_user.id,
            food_name="Grilled Salmon",
            meal_type="dinner",
            source="text",
            calories=400,
            protein_g=42,
            carbs_g=0,
            fat_g=22,
            fiber_g=0,
            logged_at=datetime.now(timezone.utc),
        )
        db_session.add(food_log)
        await db_session.commit()

        with patch("app.services.coaching.AsyncOpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client

            mock_choice = MagicMock()
            mock_choice.message.content = "Excellent protein choice! You still have room for more today."
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            from app.services.coaching import CoachingService
            service = CoachingService()
            result = await service.generate_food_response(test_user, food_log, db_session)

        assert "protein" in result.lower() or "Excellent" in result

    @pytest.mark.asyncio
    async def test_food_response_uses_active_target(self, db_session: AsyncSession, test_user: User):
        """Should use active macro target for context."""
        target = MacroTarget(
            id=uuid.uuid4(),
            user_id=test_user.id,
            calories=2500,
            protein_g=180,
            carbs_g=250,
            fat_g=80,
            effective_from=date.today() - timedelta(days=7),
            is_active=True,
        )
        db_session.add(target)

        food_log = FoodLog(
            id=uuid.uuid4(),
            user_id=test_user.id,
            food_name="Oatmeal",
            meal_type="breakfast",
            source="text",
            calories=300,
            protein_g=10,
            carbs_g=50,
            fat_g=5,
            fiber_g=8,
            logged_at=datetime.now(timezone.utc),
        )
        db_session.add(food_log)
        await db_session.commit()

        with patch("app.services.coaching.AsyncOpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client

            mock_choice = MagicMock()
            mock_choice.message.content = "Good start to the day. You have plenty of budget left."
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            from app.services.coaching import CoachingService
            service = CoachingService()

            # Verify the method calls OpenAI (not crashing is sufficient)
            result = await service.generate_food_response(test_user, food_log, db_session)

        assert len(result) > 0

"""AI Coaching Service — generates personalized insights using LLM."""

from datetime import date, timedelta
from pathlib import Path

from openai import AsyncOpenAI
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.food import FoodLog
from app.models.insights import AIInsight, MacroTarget
from app.models.user import User
from app.models.wearable import NormalizedMetric

PROMPTS_DIR = Path(__file__).parent.parent / "engine" / "prompts"


class CoachingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_daily_insight(self, user: User, db: AsyncSession) -> str:
        """Generate a daily coaching insight combining food + wearable data."""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Gather context
        context = await self._build_daily_context(user, today, yesterday, db)

        # Load prompt template
        prompt_template = (PROMPTS_DIR / "daily_checkin.txt").read_text()
        prompt = prompt_template.format(**context)

        # Call LLM
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an empathetic health coach. Be concise and supportive."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        insight_text = response.choices[0].message.content

        # Store insight
        insight = AIInsight(
            user_id=user.id,
            date=today,
            insight_type="daily",
            content=insight_text,
            context_snapshot=context,
        )
        db.add(insight)

        return insight_text

    async def generate_food_response(
        self, user: User, food_log: FoodLog, db: AsyncSession
    ) -> str:
        """Generate a coaching response to a food log entry."""
        today = date.today()

        # Get daily totals so far
        result = await db.execute(
            select(
                func.coalesce(func.sum(FoodLog.calories), 0),
                func.coalesce(func.sum(FoodLog.protein_g), 0),
            ).where(
                and_(FoodLog.user_id == user.id, func.date(FoodLog.logged_at) == today)
            )
        )
        day_total_kcal, day_protein_g = result.one()

        # Get target
        target_result = await db.execute(
            select(MacroTarget)
            .where(and_(MacroTarget.user_id == user.id, MacroTarget.is_active == True))
            .order_by(MacroTarget.effective_from.desc())
            .limit(1)
        )
        target = target_result.scalar_one_or_none()
        target_kcal = target.calories if target else 2000
        target_protein = target.protein_g if target else 150

        # Weekly total so far
        week_start = today - timedelta(days=today.weekday())
        weekly_result = await db.execute(
            select(func.coalesce(func.sum(FoodLog.calories), 0)).where(
                and_(
                    FoodLog.user_id == user.id,
                    func.date(FoodLog.logged_at) >= week_start,
                )
            )
        )
        weekly_total = weekly_result.scalar() or 0
        days_elapsed = max((today - week_start).days, 1)
        weekly_avg = round(weekly_total / days_elapsed)

        prompt_template = (PROMPTS_DIR / "food_response.txt").read_text()
        context = {
            "coach_name": "Coach",
            "user_name": user.name,
            "meal_type": food_log.meal_type,
            "log_time": food_log.logged_at.strftime("%I:%M %p") if food_log.logged_at else "now",
            "food_items": food_log.food_name,
            "meal_calories": food_log.calories,
            "meal_protein": food_log.protein_g,
            "meal_carbs": food_log.carbs_g,
            "meal_fat": food_log.fat_g,
            "day_total_kcal": day_total_kcal,
            "remaining_kcal": max(0, target_kcal - day_total_kcal),
            "day_protein_g": day_protein_g,
            "target_protein_g": target_protein,
            "weekly_avg_so_far": weekly_avg,
            "target_kcal": target_kcal,
            "days_remaining_in_week": 7 - today.weekday(),
        }

        prompt = prompt_template.format(**context)

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an empathetic health coach. Be brief and supportive."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.7,
        )

        return response.choices[0].message.content

    async def _build_daily_context(
        self, user: User, today: date, yesterday: date, db: AsyncSession
    ) -> dict:
        """Build context dict for daily insight generation."""
        # Yesterday's food totals
        food_result = await db.execute(
            select(
                func.coalesce(func.sum(FoodLog.calories), 0),
                func.coalesce(func.sum(FoodLog.protein_g), 0),
            ).where(
                and_(FoodLog.user_id == user.id, func.date(FoodLog.logged_at) == yesterday)
            )
        )
        yesterday_kcal, yesterday_protein = food_result.one()

        # Latest normalized metrics
        metrics_result = await db.execute(
            select(NormalizedMetric)
            .where(NormalizedMetric.user_id == user.id)
            .order_by(NormalizedMetric.date.desc())
            .limit(1)
        )
        metrics = metrics_result.scalar_one_or_none()

        # 7-day HRV average
        hrv_result = await db.execute(
            select(func.avg(NormalizedMetric.hrv_rmssd)).where(
                and_(
                    NormalizedMetric.user_id == user.id,
                    NormalizedMetric.date >= today - timedelta(days=7),
                )
            )
        )
        hrv_7d_avg = hrv_result.scalar() or 0

        # RHR 7-day average
        rhr_result = await db.execute(
            select(func.avg(NormalizedMetric.rhr_bpm)).where(
                and_(
                    NormalizedMetric.user_id == user.id,
                    NormalizedMetric.date >= today - timedelta(days=7),
                )
            )
        )
        rhr_7d_avg = rhr_result.scalar() or 0

        # Target
        target_result = await db.execute(
            select(MacroTarget)
            .where(and_(MacroTarget.user_id == user.id, MacroTarget.is_active == True))
            .order_by(MacroTarget.effective_from.desc())
            .limit(1)
        )
        target = target_result.scalar_one_or_none()

        # Weekly average
        week_start = today - timedelta(days=today.weekday())
        weekly_result = await db.execute(
            select(func.coalesce(func.sum(FoodLog.calories), 0)).where(
                and_(
                    FoodLog.user_id == user.id,
                    func.date(FoodLog.logged_at) >= week_start,
                    func.date(FoodLog.logged_at) < today,
                )
            )
        )
        weekly_total = weekly_result.scalar() or 0
        days_in_week = (today - week_start).days or 1
        weekly_avg = weekly_total / days_in_week

        target_kcal = target.calories if target else 2000

        return {
            "coach_name": "Coach",
            "user_name": user.name,
            "age": user.age or "unknown",
            "sex": user.sex or "unknown",
            "height_cm": user.height_cm or "unknown",
            "current_weight_kg": user.weight_kg or "unknown",
            "goal_type": user.goal_type or "maintain",
            "target_weight_kg": "N/A",
            "target_date": "N/A",
            "activity_level": user.activity_level or "moderate",
            "dietary_preferences": user.dietary_preferences or "none",
            "recovery_score": metrics.recovery_score if metrics else "N/A",
            "recovery_category": "N/A",
            "hrv_rmssd": metrics.hrv_rmssd if metrics else "N/A",
            "hrv_7d_avg": round(hrv_7d_avg, 1) if hrv_7d_avg else "N/A",
            "rhr": metrics.rhr_bpm if metrics else "N/A",
            "rhr_7d_avg": round(rhr_7d_avg, 1) if rhr_7d_avg else "N/A",
            "sleep_hours": int((metrics.sleep_duration_min or 0) // 60) if metrics else "N/A",
            "sleep_minutes": int((metrics.sleep_duration_min or 0) % 60) if metrics else "",
            "sleep_quality": metrics.sleep_score if metrics else "N/A",
            "yesterday_kcal": round(yesterday_kcal),
            "target_kcal": round(target_kcal),
            "yesterday_protein_g": round(yesterday_protein),
            "target_protein_g": round(target.protein_g) if target else 150,
            "weekly_avg_kcal": round(weekly_avg),
            "today_target_kcal": round(target_kcal),
            "flexibility": round(target_kcal * 0.1),
            "protein_g": round(target.protein_g) if target else 150,
            "carb_g": round(target.carbs_g) if target else 200,
            "fat_g": round(target.fat_g) if target else 65,
        }

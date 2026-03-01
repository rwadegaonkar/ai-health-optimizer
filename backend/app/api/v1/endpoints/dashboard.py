from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.food import FoodLog
from app.models.insights import AIInsight, MacroTarget
from app.models.schemas import DashboardData, DailySummary, MacroTargetResponse, NormalizedMetricResponse, InsightResponse
from app.models.user import User
from app.models.wearable import NormalizedMetric

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardData)
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    week_ago = today - timedelta(days=7)

    # Today's food summary
    food_result = await db.execute(
        select(
            func.coalesce(func.sum(FoodLog.calories), 0).label("total_calories"),
            func.coalesce(func.sum(FoodLog.protein_g), 0).label("total_protein_g"),
            func.coalesce(func.sum(FoodLog.carbs_g), 0).label("total_carbs_g"),
            func.coalesce(func.sum(FoodLog.fat_g), 0).label("total_fat_g"),
            func.coalesce(func.sum(FoodLog.fiber_g), 0).label("total_fiber_g"),
            func.count(FoodLog.id).label("meal_count"),
        ).where(
            and_(FoodLog.user_id == user.id, func.date(FoodLog.logged_at) == today)
        )
    )
    food_row = food_result.one()

    # Current macro targets
    target_result = await db.execute(
        select(MacroTarget)
        .where(and_(MacroTarget.user_id == user.id, MacroTarget.is_active == True))
        .order_by(MacroTarget.effective_from.desc())
        .limit(1)
    )
    target = target_result.scalar_one_or_none()

    today_summary = DailySummary(
        date=today,
        total_calories=food_row.total_calories,
        total_protein_g=food_row.total_protein_g,
        total_carbs_g=food_row.total_carbs_g,
        total_fat_g=food_row.total_fat_g,
        total_fiber_g=food_row.total_fiber_g,
        meal_count=food_row.meal_count,
        target_calories=target.calories if target else None,
        target_protein_g=target.protein_g if target else None,
        target_carbs_g=target.carbs_g if target else None,
        target_fat_g=target.fat_g if target else None,
    )

    # Latest normalized metrics
    metrics_result = await db.execute(
        select(NormalizedMetric)
        .where(NormalizedMetric.user_id == user.id)
        .order_by(NormalizedMetric.date.desc())
        .limit(1)
    )
    latest_metrics = metrics_result.scalar_one_or_none()

    # Latest AI insight
    insight_result = await db.execute(
        select(AIInsight)
        .where(AIInsight.user_id == user.id)
        .order_by(AIInsight.date.desc())
        .limit(1)
    )
    latest_insight = insight_result.scalar_one_or_none()

    # Weekly calorie data (last 7 days)
    weekly_calories = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        cal_result = await db.execute(
            select(func.coalesce(func.sum(FoodLog.calories), 0)).where(
                and_(FoodLog.user_id == user.id, func.date(FoodLog.logged_at) == d)
            )
        )
        weekly_calories.append({"date": d.isoformat(), "calories": cal_result.scalar()})

    # Weekly sleep data (last 7 days)
    sleep_result = await db.execute(
        select(NormalizedMetric)
        .where(
            and_(
                NormalizedMetric.user_id == user.id,
                NormalizedMetric.date >= week_ago,
                NormalizedMetric.date <= today,
            )
        )
        .order_by(NormalizedMetric.date)
    )
    weekly_sleep = [
        {
            "date": m.date.isoformat(),
            "sleep_hours": round(m.sleep_duration_min / 60, 1) if m.sleep_duration_min else None,
            "hrv": m.hrv_rmssd,
            "recovery": m.recovery_score,
        }
        for m in sleep_result.scalars().all()
    ]

    return DashboardData(
        today_summary=today_summary,
        current_targets=MacroTargetResponse.model_validate(target) if target else None,
        latest_metrics=NormalizedMetricResponse.model_validate(latest_metrics) if latest_metrics else None,
        latest_insight=InsightResponse.model_validate(latest_insight) if latest_insight else None,
        weekly_calories=weekly_calories,
        weekly_sleep=weekly_sleep,
    )

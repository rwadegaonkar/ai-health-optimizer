from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.insights import AIInsight, WeeklySummary, MacroTarget, UserGoal
from app.models.schemas import (
    GoalCreate,
    GoalResponse,
    InsightResponse,
    MacroTargetCreate,
    MacroTargetResponse,
    WeeklySummaryResponse,
)
from app.models.user import User

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/daily", response_model=InsightResponse | None)
async def get_daily_insight(
    target_date: date = Query(default_factory=date.today),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIInsight).where(
            and_(
                AIInsight.user_id == user.id,
                AIInsight.date == target_date,
                AIInsight.insight_type == "daily",
            )
        )
    )
    return result.scalar_one_or_none()


@router.get("/weekly", response_model=list[WeeklySummaryResponse])
async def get_weekly_summaries(
    weeks: int = Query(default=4, ge=1, le=12),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WeeklySummary)
        .where(WeeklySummary.user_id == user.id)
        .order_by(WeeklySummary.week_start.desc())
        .limit(weeks)
    )
    return result.scalars().all()


# ─── Macro Targets ──────────────────────────────────────

@router.post("/targets", response_model=MacroTargetResponse, status_code=201)
async def set_macro_targets(
    data: MacroTargetCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Deactivate previous targets
    result = await db.execute(
        select(MacroTarget).where(
            and_(MacroTarget.user_id == user.id, MacroTarget.is_active == True)
        )
    )
    for old_target in result.scalars().all():
        old_target.is_active = False
        db.add(old_target)

    target = MacroTarget(
        user_id=user.id,
        calories=data.calories,
        protein_g=data.protein_g,
        carbs_g=data.carbs_g,
        fat_g=data.fat_g,
        effective_from=data.effective_from,
    )
    db.add(target)
    await db.flush()
    return target


@router.get("/targets/current", response_model=MacroTargetResponse | None)
async def get_current_targets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MacroTarget)
        .where(and_(MacroTarget.user_id == user.id, MacroTarget.is_active == True))
        .order_by(MacroTarget.effective_from.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ─── Goals ──────────────────────────────────────────────

@router.post("/goals", response_model=GoalResponse, status_code=201)
async def create_goal(
    data: GoalCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    goal = UserGoal(
        user_id=user.id,
        goal_type=data.goal_type,
        target_value=data.target_value,
        current_value=data.current_value,
        unit=data.unit,
        start_date=data.start_date,
        target_date=data.target_date,
    )
    db.add(goal)
    await db.flush()
    return goal


@router.get("/goals", response_model=list[GoalResponse])
async def list_goals(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserGoal)
        .where(and_(UserGoal.user_id == user.id, UserGoal.status == "active"))
        .order_by(UserGoal.created_at.desc())
    )
    return result.scalars().all()

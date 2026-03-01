import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.food import FoodLog, FoodImage, LogSource
from app.models.insights import MacroTarget
from app.models.schemas import (
    DailySummary,
    FoodLogCreate,
    FoodLogResponse,
    FoodLogUpdate,
    FoodSearchResult,
    PhotoLogResponse,
    PhotoRecognitionResult,
)
from app.models.user import User
from app.services.nutrition import NutritionService
from app.services.food_vision import FoodVisionService

router = APIRouter(prefix="/food", tags=["food"])


@router.get("/search", response_model=list[FoodSearchResult])
async def search_food(
    q: str = Query(min_length=2, max_length=200),
    user: User = Depends(get_current_user),
):
    service = NutritionService()
    results = await service.search(q)
    return results


@router.post("/log", response_model=FoodLogResponse, status_code=status.HTTP_201_CREATED)
async def create_food_log(
    data: FoodLogCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    food_log = FoodLog(
        user_id=user.id,
        food_name=data.food_name,
        brand_name=data.brand_name,
        meal_type=data.meal_type,
        source=LogSource.TEXT,
        calories=data.calories,
        protein_g=data.protein_g,
        carbs_g=data.carbs_g,
        fat_g=data.fat_g,
        fiber_g=data.fiber_g,
        serving_size=data.serving_size,
        serving_qty=data.serving_qty,
        serving_weight_g=data.serving_weight_g,
        nutrition_source="manual",
        logged_at=data.logged_at or datetime.now(timezone.utc),
    )
    db.add(food_log)
    await db.flush()
    return food_log


@router.get("/logs", response_model=list[FoodLogResponse])
async def list_food_logs(
    target_date: date = Query(default_factory=lambda: date.today()),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FoodLog)
        .where(
            and_(
                FoodLog.user_id == user.id,
                func.date(FoodLog.logged_at) == target_date,
            )
        )
        .order_by(FoodLog.logged_at)
    )
    return result.scalars().all()


@router.get("/summary", response_model=DailySummary)
async def daily_summary(
    target_date: date = Query(default_factory=lambda: date.today()),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            func.coalesce(func.sum(FoodLog.calories), 0).label("total_calories"),
            func.coalesce(func.sum(FoodLog.protein_g), 0).label("total_protein_g"),
            func.coalesce(func.sum(FoodLog.carbs_g), 0).label("total_carbs_g"),
            func.coalesce(func.sum(FoodLog.fat_g), 0).label("total_fat_g"),
            func.coalesce(func.sum(FoodLog.fiber_g), 0).label("total_fiber_g"),
            func.count(FoodLog.id).label("meal_count"),
        ).where(
            and_(
                FoodLog.user_id == user.id,
                func.date(FoodLog.logged_at) == target_date,
            )
        )
    )
    row = result.one()

    # Get active macro target
    target_result = await db.execute(
        select(MacroTarget)
        .where(
            and_(
                MacroTarget.user_id == user.id,
                MacroTarget.is_active == True,
                MacroTarget.effective_from <= target_date,
            )
        )
        .order_by(MacroTarget.effective_from.desc())
        .limit(1)
    )
    target = target_result.scalar_one_or_none()

    return DailySummary(
        date=target_date,
        total_calories=row.total_calories,
        total_protein_g=row.total_protein_g,
        total_carbs_g=row.total_carbs_g,
        total_fat_g=row.total_fat_g,
        total_fiber_g=row.total_fiber_g,
        meal_count=row.meal_count,
        target_calories=target.calories if target else None,
        target_protein_g=target.protein_g if target else None,
        target_carbs_g=target.carbs_g if target else None,
        target_fat_g=target.fat_g if target else None,
    )


@router.put("/logs/{log_id}", response_model=FoodLogResponse)
async def update_food_log(
    log_id: uuid.UUID,
    data: FoodLogUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FoodLog).where(and_(FoodLog.id == log_id, FoodLog.user_id == user.id))
    )
    food_log = result.scalar_one_or_none()
    if not food_log:
        raise HTTPException(status_code=404, detail="Food log not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(food_log, field, value)

    db.add(food_log)
    await db.flush()
    return food_log


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food_log(
    log_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FoodLog).where(and_(FoodLog.id == log_id, FoodLog.user_id == user.id))
    )
    food_log = result.scalar_one_or_none()
    if not food_log:
        raise HTTPException(status_code=404, detail="Food log not found")

    await db.delete(food_log)


@router.post("/log-photo", response_model=PhotoLogResponse, status_code=status.HTTP_201_CREATED)
async def log_food_photo(
    file: UploadFile = File(...),
    meal_type: str = Query(default="snack", pattern="^(breakfast|lunch|dinner|snack)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate file type
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are supported")

    vision_service = FoodVisionService()
    image_path, recognition = await vision_service.recognize_food(file, user)

    needs_confirmation = recognition.confidence < 0.7

    # Create food log entry
    food_log = FoodLog(
        user_id=user.id,
        food_name=recognition.food_name,
        meal_type=meal_type,
        source=LogSource.PHOTO,
        calories=recognition.estimated_calories,
        protein_g=recognition.protein_g,
        carbs_g=recognition.carbs_g,
        fat_g=recognition.fat_g,
        fiber_g=recognition.fiber_g,
        serving_size=recognition.serving_size,
        confidence_score=recognition.confidence,
        nutrition_source="ai_vision",
        logged_at=datetime.now(timezone.utc),
    )
    db.add(food_log)
    await db.flush()

    # Store image metadata
    food_image = FoodImage(
        food_log_id=food_log.id,
        image_path=image_path,
        ai_response_raw=recognition.model_dump(),
        ai_food_name=recognition.food_name,
        ai_confidence=recognition.confidence,
    )
    db.add(food_image)
    await db.flush()

    return PhotoLogResponse(
        food_log_id=food_log.id,
        recognition=recognition,
        needs_confirmation=needs_confirmation,
        image_path=image_path,
    )

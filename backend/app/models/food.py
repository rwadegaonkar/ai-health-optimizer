import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class LogSource(str, enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    QUICK_ADD = "quick_add"


class FoodLog(Base):
    __tablename__ = "food_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    food_name: Mapped[str] = mapped_column(String(300), nullable=False)
    brand_name: Mapped[str | None] = mapped_column(String(200))
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default=LogSource.TEXT)

    # Nutrition
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    fat_g: Mapped[float] = mapped_column(Float, default=0)
    fiber_g: Mapped[float] = mapped_column(Float, default=0)

    # Serving
    serving_size: Mapped[str | None] = mapped_column(String(100))
    serving_qty: Mapped[float] = mapped_column(Float, default=1)
    serving_weight_g: Mapped[float | None] = mapped_column(Float)

    # AI confidence (for photo-logged items)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    nutrition_source: Mapped[str | None] = mapped_column(String(50))

    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="food_logs")
    image = relationship("FoodImage", back_populates="food_log", uselist=False)


class FoodImage(Base):
    __tablename__ = "food_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    food_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("food_logs.id"), nullable=False, unique=True
    )

    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    ai_response_raw: Mapped[dict | None] = mapped_column(JSONB)
    ai_food_name: Mapped[str | None] = mapped_column(String(300))
    ai_confidence: Mapped[float | None] = mapped_column(Float)
    user_corrected: Mapped[bool] = mapped_column(Boolean, default=False)
    correction_data: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    food_log = relationship("FoodLog", back_populates="image")

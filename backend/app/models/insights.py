import uuid
from datetime import datetime, date, timezone

from sqlalchemy import String, Float, DateTime, Date, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class InsightType(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    RECOVERY_ALERT = "recovery_alert"
    TREND = "trend"
    MILESTONE = "milestone"


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    insight_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[dict | None] = mapped_column(JSONB)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)

    # Nutrition averages
    avg_calories: Mapped[float | None] = mapped_column(Float)
    avg_protein_g: Mapped[float | None] = mapped_column(Float)
    avg_carbs_g: Mapped[float | None] = mapped_column(Float)
    avg_fat_g: Mapped[float | None] = mapped_column(Float)
    calorie_target: Mapped[float | None] = mapped_column(Float)
    calorie_delta: Mapped[float | None] = mapped_column(Float)

    # Wearable averages
    avg_sleep_min: Mapped[float | None] = mapped_column(Float)
    avg_hrv: Mapped[float | None] = mapped_column(Float)
    avg_rhr: Mapped[float | None] = mapped_column(Float)
    avg_steps: Mapped[int | None] = mapped_column(Integer)
    avg_recovery: Mapped[float | None] = mapped_column(Float)

    # Body
    weight_start: Mapped[float | None] = mapped_column(Float)
    weight_end: Mapped[float | None] = mapped_column(Float)
    weight_change: Mapped[float | None] = mapped_column(Float)

    # AI summary
    ai_summary: Mapped[str | None] = mapped_column(Text)
    adjustments: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class MacroTarget(Base):
    __tablename__ = "macro_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="macro_targets")


class UserGoal(Base):
    __tablename__ = "user_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="goals")


class TrendFlag(Base):
    __tablename__ = "trend_flags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    flag_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    data: Mapped[dict | None] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(default=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

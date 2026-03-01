import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Float, Integer, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ActivityLevel(str, enum.Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"


class GoalType(str, enum.Enum):
    LOSE_WEIGHT = "lose_weight"
    GAIN_MUSCLE = "gain_muscle"
    MAINTAIN = "maintain"
    RECOMPOSITION = "recomposition"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Physical profile
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    age: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(String(10))
    activity_level: Mapped[str | None] = mapped_column(
        SAEnum(ActivityLevel, name="activity_level_enum", create_constraint=False),
        default=ActivityLevel.MODERATELY_ACTIVE,
    )
    goal_type: Mapped[str | None] = mapped_column(
        SAEnum(GoalType, name="goal_type_enum", create_constraint=False),
        default=GoalType.MAINTAIN,
    )

    # Preferences
    dietary_preferences: Mapped[str | None] = mapped_column(String(500))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    coach_personality: Mapped[str] = mapped_column(String(50), default="balanced")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    food_logs = relationship("FoodLog", back_populates="user", lazy="selectin")
    wearable_connections = relationship("WearableConnection", back_populates="user", lazy="selectin")
    macro_targets = relationship("MacroTarget", back_populates="user", lazy="selectin")
    goals = relationship("UserGoal", back_populates="user", lazy="selectin")

import uuid
from datetime import datetime, date, timezone

from sqlalchemy import String, Float, Boolean, DateTime, Date, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class WearableProvider(str, enum.Enum):
    FITBIT = "fitbit"
    APPLE_HEALTH = "apple_health"
    GARMIN = "garmin"


class WearableConnection(Base):
    __tablename__ = "wearable_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    provider_user_id: Mapped[str | None] = mapped_column(String(100))

    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[str | None] = mapped_column(String(500))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User", back_populates="wearable_connections")


class WearableRawData(Base):
    __tablename__ = "wearable_raw_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(30), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class NormalizedMetric(Base):
    __tablename__ = "normalized_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)

    # Sleep
    sleep_duration_min: Mapped[float | None] = mapped_column(Float)
    sleep_deep_min: Mapped[float | None] = mapped_column(Float)
    sleep_rem_min: Mapped[float | None] = mapped_column(Float)
    sleep_light_min: Mapped[float | None] = mapped_column(Float)
    sleep_wake_min: Mapped[float | None] = mapped_column(Float)
    sleep_efficiency: Mapped[float | None] = mapped_column(Float)
    sleep_score: Mapped[float | None] = mapped_column(Float)

    # Heart
    hrv_rmssd: Mapped[float | None] = mapped_column(Float)
    rhr_bpm: Mapped[float | None] = mapped_column(Float)

    # Activity
    steps: Mapped[int | None] = mapped_column(Integer)
    active_minutes: Mapped[int | None] = mapped_column(Integer)
    calories_burned: Mapped[float | None] = mapped_column(Float)
    distance_km: Mapped[float | None] = mapped_column(Float)

    # Computed
    recovery_score: Mapped[float | None] = mapped_column(Float)
    training_load: Mapped[float | None] = mapped_column(Float)
    readiness_score: Mapped[float | None] = mapped_column(Float)

    # Source
    primary_source: Mapped[str | None] = mapped_column(String(30))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

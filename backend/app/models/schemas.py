"""Pydantic schemas for API request/response validation."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, computed_field


# ─── Auth ───────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


# ─── User ───────────────────────────────────────────────

class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    height_cm: float | None = None
    weight_kg: float | None = None
    age: int | None = None
    sex: str | None = None
    activity_level: str | None = None
    goal_type: str | None = None
    dietary_preferences: str | None = None
    timezone: str = "UTC"
    coach_personality: str = "balanced"

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def profile_completed(self) -> bool:
        return all([
            self.height_cm is not None,
            self.weight_kg is not None,
            self.age is not None,
            self.sex is not None,
        ])


class UserProfileUpdate(BaseModel):
    name: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    age: int | None = None
    sex: str | None = None
    activity_level: str | None = None
    goal_type: str | None = None
    dietary_preferences: str | None = None
    timezone: str | None = None
    coach_personality: str | None = None


# ─── Food Logging ───────────────────────────────────────

class FoodLogCreate(BaseModel):
    food_name: str = Field(max_length=300)
    brand_name: str | None = None
    meal_type: str = Field(pattern="^(breakfast|lunch|dinner|snack)$")
    calories: float = Field(ge=0)
    protein_g: float = Field(ge=0, default=0)
    carbs_g: float = Field(ge=0, default=0)
    fat_g: float = Field(ge=0, default=0)
    fiber_g: float = Field(ge=0, default=0)
    serving_size: str | None = None
    serving_qty: float = 1
    serving_weight_g: float | None = None
    logged_at: datetime | None = None


class FoodLogUpdate(BaseModel):
    food_name: str | None = None
    meal_type: str | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    serving_size: str | None = None
    serving_qty: float | None = None


class FoodLogResponse(BaseModel):
    id: uuid.UUID
    food_name: str
    brand_name: str | None
    meal_type: str
    source: str
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    serving_size: str | None
    serving_qty: float
    serving_weight_g: float | None
    confidence_score: float | None
    logged_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class DailySummary(BaseModel):
    date: date
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    meal_count: int
    target_calories: float | None = None
    target_protein_g: float | None = None
    target_carbs_g: float | None = None
    target_fat_g: float | None = None


# ─── Food Search ────────────────────────────────────────

class FoodSearchResult(BaseModel):
    food_name: str
    brand_name: str | None = None
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    serving_size: str | None = None
    serving_weight_g: float | None = None
    source: str = "nutritionix"
    thumbnail: str | None = None


# ─── Photo Food Logging ────────────────────────────────

class PhotoRecognitionResult(BaseModel):
    food_name: str
    estimated_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0
    serving_size: str | None = None
    confidence: float
    notes: str | None = None


class PhotoLogResponse(BaseModel):
    food_log_id: uuid.UUID
    recognition: PhotoRecognitionResult
    needs_confirmation: bool
    image_path: str


# ─── Macro Targets ──────────────────────────────────────

class MacroTargetCreate(BaseModel):
    calories: float = Field(gt=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    effective_from: date


class MacroTargetResponse(BaseModel):
    id: uuid.UUID
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    effective_from: date
    is_active: bool

    model_config = {"from_attributes": True}


# ─── Goals ──────────────────────────────────────────────

class GoalCreate(BaseModel):
    goal_type: str
    target_value: float
    current_value: float | None = None
    unit: str
    start_date: date
    target_date: date | None = None


class GoalResponse(BaseModel):
    id: uuid.UUID
    goal_type: str
    target_value: float
    current_value: float | None
    unit: str
    start_date: date
    target_date: date | None
    status: str

    model_config = {"from_attributes": True}


# ─── Wearable ──────────────────────────────────────────

class WearableConnectionResponse(BaseModel):
    id: uuid.UUID
    provider: str
    is_active: bool
    last_sync_at: datetime | None

    model_config = {"from_attributes": True}


class NormalizedMetricResponse(BaseModel):
    date: date
    sleep_duration_min: float | None
    sleep_score: float | None
    hrv_rmssd: float | None
    rhr_bpm: float | None
    steps: int | None
    active_minutes: int | None
    calories_burned: float | None
    recovery_score: float | None
    readiness_score: float | None

    model_config = {"from_attributes": True}


# ─── Insights ──────────────────────────────────────────

class InsightResponse(BaseModel):
    id: uuid.UUID
    date: date
    insight_type: str
    content: str
    recommendations: dict | None

    model_config = {"from_attributes": True}


class WeeklySummaryResponse(BaseModel):
    id: uuid.UUID
    week_start: date
    avg_calories: float | None
    avg_protein_g: float | None
    avg_carbs_g: float | None
    avg_fat_g: float | None
    calorie_target: float | None
    calorie_delta: float | None
    avg_sleep_min: float | None
    avg_hrv: float | None
    avg_steps: int | None
    avg_recovery: float | None
    weight_change: float | None
    ai_summary: str | None

    model_config = {"from_attributes": True}


# ─── Dashboard ─────────────────────────────────────────

class DashboardData(BaseModel):
    today_summary: DailySummary | None
    current_targets: MacroTargetResponse | None
    latest_metrics: NormalizedMetricResponse | None
    latest_insight: InsightResponse | None
    weekly_calories: list[dict]
    weekly_sleep: list[dict]

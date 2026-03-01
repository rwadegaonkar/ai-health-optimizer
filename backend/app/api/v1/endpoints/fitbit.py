import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.integrations.fitbit.client import FitbitOAuth2, FitbitDataClient
from app.models.user import User
from app.models.wearable import WearableConnection, WearableRawData, NormalizedMetric

router = APIRouter(prefix="/integrations/fitbit", tags=["fitbit"])


@router.get("/connect")
async def connect_fitbit(user: User = Depends(get_current_user)):
    """Redirect user to Fitbit OAuth2 authorization page."""
    oauth = FitbitOAuth2()
    state = str(user.id)  # Use user ID as state for simplicity
    auth_url = oauth.get_authorization_url(state=state)
    return {"authorization_url": auth_url}


@router.get("/callback")
async def fitbit_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth2 callback from Fitbit."""
    oauth = FitbitOAuth2()

    try:
        token_data = await oauth.exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {e}")

    user_id = uuid.UUID(state)

    # Upsert wearable connection
    result = await db.execute(
        select(WearableConnection).where(
            and_(
                WearableConnection.user_id == user_id,
                WearableConnection.provider == "fitbit",
            )
        )
    )
    connection = result.scalar_one_or_none()

    if connection:
        connection.access_token_encrypted = token_data["access_token"]
        connection.refresh_token_encrypted = token_data["refresh_token"]
        connection.token_expires_at = datetime.now(timezone.utc) + \
            __import__("datetime").timedelta(seconds=token_data.get("expires_in", 28800))
        connection.provider_user_id = token_data.get("user_id")
        connection.is_active = True
    else:
        connection = WearableConnection(
            user_id=user_id,
            provider="fitbit",
            provider_user_id=token_data.get("user_id"),
            access_token_encrypted=token_data["access_token"],
            refresh_token_encrypted=token_data["refresh_token"],
            token_expires_at=datetime.now(timezone.utc) + \
                __import__("datetime").timedelta(seconds=token_data.get("expires_in", 28800)),
            scopes=token_data.get("scope", ""),
        )

    db.add(connection)
    await db.flush()

    # Redirect to frontend success page
    return RedirectResponse(url="http://localhost:3000/settings?fitbit=connected")


@router.post("/sync")
async def sync_fitbit_data(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a sync of today's Fitbit data."""
    result = await db.execute(
        select(WearableConnection).where(
            and_(
                WearableConnection.user_id == user.id,
                WearableConnection.provider == "fitbit",
                WearableConnection.is_active == True,
            )
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Fitbit not connected")

    client = FitbitDataClient(access_token=connection.access_token_encrypted)

    from datetime import date
    today = date.today()

    try:
        data = await client.sync_daily_data(today)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Fitbit API error: {e}")

    # Store raw data
    for metric_type, value in data.items():
        if metric_type == "date" or value is None:
            continue
        raw = WearableRawData(
            user_id=user.id,
            provider="fitbit",
            metric_type=metric_type,
            value_json=value,
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(raw)

    # Create/update normalized metrics
    normalized = await _normalize_fitbit_data(user.id, today, data, db)

    connection.last_sync_at = datetime.now(timezone.utc)
    db.add(connection)
    await db.flush()

    return {"status": "synced", "date": today.isoformat(), "metrics": data}


async def _normalize_fitbit_data(
    user_id: uuid.UUID, target_date, data: dict, db: AsyncSession
) -> NormalizedMetric:
    """Convert raw Fitbit data into normalized metrics."""
    from datetime import date as date_type

    result = await db.execute(
        select(NormalizedMetric).where(
            and_(
                NormalizedMetric.user_id == user_id,
                NormalizedMetric.date == target_date,
            )
        )
    )
    metric = result.scalar_one_or_none()

    if not metric:
        metric = NormalizedMetric(user_id=user_id, date=target_date)

    sleep = data.get("sleep")
    if sleep:
        total_min = sleep.get("total_minutes", 0)
        metric.sleep_duration_min = total_min
        metric.sleep_deep_min = sleep.get("deep_minutes")
        metric.sleep_rem_min = sleep.get("rem_minutes")
        metric.sleep_light_min = sleep.get("light_minutes")
        metric.sleep_wake_min = sleep.get("wake_minutes")
        metric.sleep_efficiency = sleep.get("efficiency")
        # Simple sleep score: weighted combination
        if total_min > 0:
            duration_score = min(100, (total_min / 480) * 100)
            deep_pct = (sleep.get("deep_minutes", 0) / total_min * 100) if total_min else 0
            metric.sleep_score = round(duration_score * 0.6 + metric.sleep_efficiency * 0.2 + min(100, deep_pct / 20 * 100) * 0.2)

    hrv = data.get("hrv")
    if hrv:
        metric.hrv_rmssd = hrv.get("rmssd")

    heart = data.get("heart_rate")
    if heart:
        metric.rhr_bpm = heart.get("resting_hr")

    activity = data.get("activity")
    if activity:
        metric.steps = activity.get("steps")
        metric.active_minutes = activity.get("active_minutes")
        metric.calories_burned = activity.get("calories_total")
        metric.distance_km = activity.get("distance_km")

    metric.primary_source = "fitbit"

    db.add(metric)
    return metric

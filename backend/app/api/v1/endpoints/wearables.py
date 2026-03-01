import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.schemas import NormalizedMetricResponse, WearableConnectionResponse
from app.models.user import User
from app.models.wearable import NormalizedMetric, WearableConnection

router = APIRouter(prefix="/wearables", tags=["wearables"])


@router.get("/connections", response_model=list[WearableConnectionResponse])
async def list_connections(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WearableConnection).where(WearableConnection.user_id == user.id)
    )
    return result.scalars().all()


@router.get("/metrics", response_model=list[NormalizedMetricResponse])
async def get_metrics(
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=7)),
    end_date: date = Query(default_factory=date.today),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NormalizedMetric)
        .where(
            and_(
                NormalizedMetric.user_id == user.id,
                NormalizedMetric.date >= start_date,
                NormalizedMetric.date <= end_date,
            )
        )
        .order_by(NormalizedMetric.date)
    )
    return result.scalars().all()


@router.get("/metrics/latest", response_model=NormalizedMetricResponse | None)
async def get_latest_metric(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NormalizedMetric)
        .where(NormalizedMetric.user_id == user.id)
        .order_by(NormalizedMetric.date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.delete("/connections/{connection_id}", status_code=204)
async def disconnect_wearable(
    connection_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WearableConnection).where(
            and_(
                WearableConnection.id == connection_id,
                WearableConnection.user_id == user.id,
            )
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection.is_active = False
    db.add(connection)

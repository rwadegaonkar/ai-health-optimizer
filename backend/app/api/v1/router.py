from fastapi import APIRouter

from app.api.v1.endpoints import auth, dashboard, fitbit, food, insights, users, wearables

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(food.router)
api_router.include_router(wearables.router)
api_router.include_router(insights.router)
api_router.include_router(dashboard.router)
api_router.include_router(fitbit.router)

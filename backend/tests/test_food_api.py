"""Tests for food logging API endpoints."""

import pytest
from httpx import AsyncClient


class TestFoodLogCRUD:
    @pytest.mark.asyncio
    async def test_create_food_log(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={
                "food_name": "Chicken Breast",
                "meal_type": "lunch",
                "calories": 165,
                "protein_g": 31,
                "carbs_g": 0,
                "fat_g": 3.6,
                "fiber_g": 0,
                "serving_size": "100g",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["food_name"] == "Chicken Breast"
        assert data["calories"] == 165
        assert data["protein_g"] == 31
        assert data["source"] == "text"

    @pytest.mark.asyncio
    async def test_list_food_logs_by_date(self, client: AsyncClient, auth_headers):
        # Create two logs
        await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Oatmeal", "meal_type": "breakfast", "calories": 300, "protein_g": 10, "carbs_g": 50, "fat_g": 5},
        )
        await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Rice and Dal", "meal_type": "lunch", "calories": 450, "protein_g": 15, "carbs_g": 70, "fat_g": 8},
        )

        from datetime import date
        today = date.today().isoformat()
        response = await client.get(f"/api/v1/food/logs?target_date={today}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_daily_summary(self, client: AsyncClient, auth_headers):
        await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Eggs", "meal_type": "breakfast", "calories": 200, "protein_g": 14, "carbs_g": 1, "fat_g": 15},
        )
        await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Salad", "meal_type": "lunch", "calories": 300, "protein_g": 10, "carbs_g": 20, "fat_g": 15},
        )

        from datetime import date
        today = date.today().isoformat()
        response = await client.get(f"/api/v1/food/summary?target_date={today}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_calories"] == 500
        assert data["total_protein_g"] == 24
        assert data["meal_count"] == 2

    @pytest.mark.asyncio
    async def test_update_food_log(self, client: AsyncClient, auth_headers):
        create_response = await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Toast", "meal_type": "breakfast", "calories": 100, "protein_g": 3, "carbs_g": 20, "fat_g": 1},
        )
        log_id = create_response.json()["id"]

        update_response = await client.put(
            f"/api/v1/food/logs/{log_id}",
            headers=auth_headers,
            json={"calories": 150, "food_name": "Toast with Butter"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["calories"] == 150
        assert update_response.json()["food_name"] == "Toast with Butter"

    @pytest.mark.asyncio
    async def test_delete_food_log(self, client: AsyncClient, auth_headers):
        create_response = await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Soda", "meal_type": "snack", "calories": 140, "protein_g": 0, "carbs_g": 39, "fat_g": 0},
        )
        log_id = create_response.json()["id"]

        delete_response = await client.delete(f"/api/v1/food/logs/{log_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        from datetime import date
        today = date.today().isoformat()
        list_response = await client.get(f"/api/v1/food/logs?target_date={today}", headers=auth_headers)
        assert len(list_response.json()) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_log(self, client: AsyncClient, auth_headers):
        response = await client.delete(
            "/api/v1/food/logs/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_meal_type(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Food", "meal_type": "brunch", "calories": 100},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_negative_calories_rejected(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/food/log",
            headers=auth_headers,
            json={"food_name": "Food", "meal_type": "lunch", "calories": -100},
        )
        assert response.status_code == 422

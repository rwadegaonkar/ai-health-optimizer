"""Nutritionix API client for food search and macro lookup."""

import httpx

from app.core.config import settings
from app.models.schemas import FoodSearchResult


class NutritionService:
    BASE_URL = "https://trackapi.nutritionix.com/v2"

    def __init__(self):
        self.headers = {
            "x-app-id": settings.NUTRITIONIX_APP_ID,
            "x-app-key": settings.NUTRITIONIX_API_KEY,
            "Content-Type": "application/json",
        }

    async def search(self, query: str) -> list[FoodSearchResult]:
        """Search for foods using Nutritionix instant endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/search/instant",
                params={"query": query},
                headers=self.headers,
                timeout=10.0,
            )

            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            # Common foods (generic items like "chicken breast")
            for item in data.get("common", [])[:5]:
                nutrients = await self._get_nutrients(item["food_name"])
                if nutrients:
                    results.append(nutrients)

            # Branded foods
            for item in data.get("branded", [])[:5]:
                results.append(
                    FoodSearchResult(
                        food_name=item.get("food_name", ""),
                        brand_name=item.get("brand_name"),
                        calories=item.get("nf_calories", 0),
                        protein_g=item.get("nf_protein", 0),
                        carbs_g=item.get("nf_total_carbohydrate", 0),
                        fat_g=item.get("nf_total_fat", 0),
                        fiber_g=item.get("nf_dietary_fiber", 0),
                        serving_size=item.get("serving_unit"),
                        serving_weight_g=item.get("serving_weight_grams"),
                        source="nutritionix",
                        thumbnail=item.get("photo", {}).get("thumb"),
                    )
                )

            return results

    async def _get_nutrients(self, food_name: str) -> FoodSearchResult | None:
        """Get detailed nutrients for a common food item."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/natural/nutrients",
                json={"query": food_name},
                headers=self.headers,
                timeout=10.0,
            )

            if response.status_code != 200:
                return None

            data = response.json()
            foods = data.get("foods", [])
            if not foods:
                return None

            food = foods[0]
            return FoodSearchResult(
                food_name=food.get("food_name", ""),
                brand_name=food.get("brand_name"),
                calories=food.get("nf_calories", 0),
                protein_g=food.get("nf_protein", 0),
                carbs_g=food.get("nf_total_carbohydrate", 0),
                fat_g=food.get("nf_total_fat", 0),
                fiber_g=food.get("nf_dietary_fiber", 0),
                serving_size=food.get("serving_unit"),
                serving_weight_g=food.get("serving_weight_grams"),
                source="nutritionix",
                thumbnail=food.get("photo", {}).get("thumb"),
            )

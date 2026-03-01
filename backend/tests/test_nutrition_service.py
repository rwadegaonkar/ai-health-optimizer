"""Tests for the Nutritionix API client."""

from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest

from app.services.nutrition import NutritionService


class TestNutritionService:
    def setup_method(self):
        self.service = NutritionService()

    @pytest.mark.asyncio
    async def test_search_returns_common_and_branded(self):
        """Search should return both common and branded food results."""
        instant_response = httpx.Response(
            200,
            json={
                "common": [{"food_name": "chicken breast"}],
                "branded": [
                    {
                        "food_name": "Protein Bar",
                        "brand_name": "Quest",
                        "nf_calories": 200,
                        "nf_protein": 21,
                        "nf_total_carbohydrate": 22,
                        "nf_total_fat": 8,
                        "nf_dietary_fiber": 14,
                        "serving_unit": "bar",
                        "serving_weight_grams": 60,
                        "photo": {"thumb": "http://example.com/thumb.jpg"},
                    }
                ],
            },
        )
        nutrients_response = httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "food_name": "chicken breast",
                        "nf_calories": 165,
                        "nf_protein": 31,
                        "nf_total_carbohydrate": 0,
                        "nf_total_fat": 3.6,
                        "nf_dietary_fiber": 0,
                        "serving_unit": "breast",
                        "serving_weight_grams": 100,
                        "photo": {"thumb": "http://example.com/chicken.jpg"},
                    }
                ]
            },
        )

        with patch("app.services.nutrition.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=instant_response)
            mock_client.post = AsyncMock(return_value=nutrients_response)

            results = await self.service.search("chicken")

        assert len(results) == 2
        assert results[0].food_name == "chicken breast"
        assert results[0].calories == 165
        assert results[0].protein_g == 31
        assert results[1].food_name == "Protein Bar"
        assert results[1].brand_name == "Quest"
        assert results[1].calories == 200

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_api_error(self):
        """Search should return empty list on non-200 status."""
        error_response = httpx.Response(500, json={"error": "Internal server error"})

        with patch("app.services.nutrition.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=error_response)

            results = await self.service.search("chicken")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self):
        """Search should handle response with no common or branded items."""
        empty_response = httpx.Response(200, json={"common": [], "branded": []})

        with patch("app.services.nutrition.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=empty_response)

            results = await self.service.search("xyznonexistent")

        assert results == []

    @pytest.mark.asyncio
    async def test_get_nutrients_returns_none_on_error(self):
        """_get_nutrients should return None on non-200 response."""
        error_response = httpx.Response(404, json={"message": "not found"})

        with patch("app.services.nutrition.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=error_response)

            result = await self.service._get_nutrients("chicken breast")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_nutrients_returns_none_on_empty_foods(self):
        """_get_nutrients should return None when foods list is empty."""
        empty_response = httpx.Response(200, json={"foods": []})

        with patch("app.services.nutrition.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=empty_response)

            result = await self.service._get_nutrients("nonexistent food")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_nutrients_parses_food_data(self):
        """_get_nutrients should correctly parse Nutritionix food data."""
        nutrients_response = httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "food_name": "oatmeal",
                        "brand_name": None,
                        "nf_calories": 150,
                        "nf_protein": 5,
                        "nf_total_carbohydrate": 27,
                        "nf_total_fat": 3,
                        "nf_dietary_fiber": 4,
                        "serving_unit": "cup",
                        "serving_weight_grams": 234,
                        "photo": {"thumb": "http://example.com/oatmeal.jpg"},
                    }
                ]
            },
        )

        with patch("app.services.nutrition.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=nutrients_response)

            result = await self.service._get_nutrients("oatmeal")

        assert result is not None
        assert result.food_name == "oatmeal"
        assert result.calories == 150
        assert result.protein_g == 5
        assert result.carbs_g == 27
        assert result.fat_g == 3
        assert result.fiber_g == 4
        assert result.serving_size == "cup"
        assert result.source == "nutritionix"

    @pytest.mark.asyncio
    async def test_search_skips_common_if_nutrients_fail(self):
        """Common items that fail nutrient lookup should be skipped."""
        instant_response = httpx.Response(
            200,
            json={
                "common": [{"food_name": "mystery food"}],
                "branded": [],
            },
        )
        nutrients_error = httpx.Response(500, json={"error": "server error"})

        with patch("app.services.nutrition.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=instant_response)
            mock_client.post = AsyncMock(return_value=nutrients_error)

            results = await self.service.search("mystery food")

        assert results == []

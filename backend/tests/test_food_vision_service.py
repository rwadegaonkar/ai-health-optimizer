"""Tests for the Food Vision Service (GPT-4o image recognition)."""

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.services.food_vision import FoodVisionService


class TestParseResponse:
    """Test _parse_response with various GPT-4o output formats."""

    def setup_method(self):
        with patch("app.services.food_vision.AsyncOpenAI"):
            self.service = FoodVisionService()

    def test_parse_valid_json(self):
        content = json.dumps({
            "food_name": "Grilled Chicken Salad",
            "estimated_calories": 350,
            "protein_g": 30,
            "carbs_g": 15,
            "fat_g": 18,
            "fiber_g": 5,
            "serving_size": "1 plate",
            "confidence": 0.85,
            "notes": "Dressing adds extra fat",
        })
        result = self.service._parse_response(content)
        assert result.food_name == "Grilled Chicken Salad"
        assert result.estimated_calories == 350
        assert result.protein_g == 30
        assert result.confidence == 0.85

    def test_parse_json_in_markdown_code_block(self):
        content = """Here's the analysis:
```json
{
    "food_name": "Dal Rice",
    "estimated_calories": 450,
    "protein_g": 15,
    "carbs_g": 60,
    "fat_g": 12,
    "fiber_g": 8,
    "serving_size": "1 plate",
    "confidence": 0.7,
    "notes": "Typical Indian meal"
}
```"""
        result = self.service._parse_response(content)
        assert result.food_name == "Dal Rice"
        assert result.estimated_calories == 450

    def test_parse_json_in_plain_code_block(self):
        content = """```
{
    "food_name": "Toast",
    "estimated_calories": 120,
    "protein_g": 3,
    "carbs_g": 20,
    "fat_g": 2,
    "fiber_g": 1,
    "serving_size": "2 slices",
    "confidence": 0.9,
    "notes": null
}
```"""
        result = self.service._parse_response(content)
        assert result.food_name == "Toast"
        assert result.estimated_calories == 120

    def test_parse_invalid_json_returns_fallback(self):
        content = "I can't recognize this image clearly."
        result = self.service._parse_response(content)
        assert result.food_name == "Unrecognized food"
        assert result.estimated_calories == 0
        assert result.confidence == 0.0
        assert "manually" in result.notes.lower()

    def test_parse_partial_json_returns_fallback(self):
        content = '{"food_name": "Broken'
        result = self.service._parse_response(content)
        assert result.food_name == "Unrecognized food"
        assert result.confidence == 0.0

    def test_parse_missing_fields_uses_defaults(self):
        content = json.dumps({
            "food_name": "Mystery Dish",
            "estimated_calories": 200,
            "protein_g": 10,
            "carbs_g": 25,
            "fat_g": 8,
        })
        result = self.service._parse_response(content)
        assert result.food_name == "Mystery Dish"
        assert result.fiber_g == 0
        assert result.confidence == 0.5  # default


class TestCompressImage:
    """Test _compress_image resizing logic."""

    def setup_method(self):
        with patch("app.services.food_vision.AsyncOpenAI"):
            self.service = FoodVisionService()

    def _make_image(self, width: int, height: int) -> bytes:
        img = Image.new("RGB", (width, height), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    def test_small_image_not_resized(self):
        image_data = self._make_image(500, 500)
        result = self.service._compress_image(image_data)
        img = Image.open(io.BytesIO(result))
        assert img.size == (500, 500)

    def test_large_image_resized(self):
        image_data = self._make_image(2000, 1500)
        result = self.service._compress_image(image_data)
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= 1024

    def test_custom_max_size(self):
        image_data = self._make_image(800, 800)
        result = self.service._compress_image(image_data, max_size=512)
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= 512


class TestSaveImage:
    """Test _save_image file writing."""

    def setup_method(self):
        with patch("app.services.food_vision.AsyncOpenAI"):
            self.service = FoodVisionService()

    @pytest.mark.asyncio
    async def test_save_image_creates_file(self, tmp_path):
        with patch("app.services.food_vision.UPLOAD_DIR", tmp_path):
            img = Image.new("RGB", (100, 100), color="blue")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            image_data = buffer.getvalue()

            path = await self.service._save_image(image_data, "test_photo.jpg")
            assert path.exists()
            assert path.suffix == ".jpg"

    @pytest.mark.asyncio
    async def test_save_image_default_extension(self, tmp_path):
        with patch("app.services.food_vision.UPLOAD_DIR", tmp_path):
            image_data = b"fake image data"
            path = await self.service._save_image(image_data, None)
            assert path.suffix == ".jpg"


class TestRecognizeFood:
    """Test the full recognize_food pipeline with mocked OpenAI."""

    def setup_method(self):
        with patch("app.services.food_vision.AsyncOpenAI"):
            self.service = FoodVisionService()

    @pytest.mark.asyncio
    async def test_recognize_food_success(self, tmp_path):
        # Create a fake upload file
        img = Image.new("RGB", (200, 200), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        mock_file = MagicMock()
        mock_file.read = AsyncMock(return_value=buffer.getvalue())
        mock_file.filename = "lunch.jpg"
        mock_file.content_type = "image/jpeg"

        mock_user = MagicMock()
        mock_user.dietary_preferences = "vegetarian"

        ai_response_json = json.dumps({
            "food_name": "Paneer Tikka",
            "estimated_calories": 300,
            "protein_g": 20,
            "carbs_g": 10,
            "fat_g": 18,
            "fiber_g": 2,
            "serving_size": "6 pieces",
            "confidence": 0.82,
            "notes": "Estimated with typical marinade",
        })

        mock_choice = MagicMock()
        mock_choice.message.content = ai_response_json
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        self.service.client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("app.services.food_vision.UPLOAD_DIR", tmp_path):
            image_path, result = await self.service.recognize_food(mock_file, mock_user)

        assert result.food_name == "Paneer Tikka"
        assert result.estimated_calories == 300
        assert result.confidence == 0.82
        assert "paneer" in result.food_name.lower() or "Paneer" in result.food_name

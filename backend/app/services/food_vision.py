"""Computer vision food recognition using OpenAI GPT-4o Vision."""

import base64
import json
import uuid
from pathlib import Path

from fastapi import UploadFile
from openai import AsyncOpenAI
from PIL import Image
import io

from app.core.config import settings
from app.models.schemas import PhotoRecognitionResult
from app.models.user import User

UPLOAD_DIR = Path("uploads/food_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

FOOD_RECOGNITION_PROMPT = """Analyze this food photo and estimate the nutritional content.

Return ONLY a valid JSON object with these fields:
{
    "food_name": "descriptive name of the food",
    "estimated_calories": <number>,
    "protein_g": <number>,
    "carbs_g": <number>,
    "fat_g": <number>,
    "fiber_g": <number>,
    "serving_size": "estimated portion description",
    "confidence": <0.0 to 1.0>,
    "notes": "any caveats about the estimation"
}

Guidelines:
- Be conservative with calorie estimates
- For Indian meals, account for oil/ghee used in cooking
- For mixed plates, estimate the combined total
- If you can identify multiple items, combine them into one total
- If the image is unclear or not food, set confidence below 0.3
- Consider typical portion sizes for the identified food
- Round macros to 1 decimal place
"""


class FoodVisionService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def recognize_food(
        self, file: UploadFile, user: User
    ) -> tuple[str, PhotoRecognitionResult]:
        """Process uploaded food image and return recognition results."""

        # Read and save the image
        image_data = await file.read()
        image_path = await self._save_image(image_data, file.filename)

        # Compress if needed
        image_data = self._compress_image(image_data)

        # Encode to base64
        b64_image = base64.b64encode(image_data).decode("utf-8")
        mime_type = file.content_type or "image/jpeg"

        # Build user context for better recognition
        context_parts = []
        if user.dietary_preferences:
            context_parts.append(f"User dietary preferences: {user.dietary_preferences}")

        prompt = FOOD_RECOGNITION_PROMPT
        if context_parts:
            prompt += "\n\nAdditional context:\n" + "\n".join(context_parts)

        # Call GPT-4o Vision
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=500,
            temperature=0.2,
        )

        # Parse response
        content = response.choices[0].message.content
        recognition = self._parse_response(content)

        return str(image_path), recognition

    def _compress_image(self, image_data: bytes, max_size: int = 1024) -> bytes:
        """Compress image if larger than max_size pixels on any side."""
        img = Image.open(io.BytesIO(image_data))

        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img_format = img.format or "JPEG"
        img.save(buffer, format=img_format, quality=85)
        return buffer.getvalue()

    async def _save_image(self, image_data: bytes, filename: str | None) -> Path:
        """Save uploaded image to disk."""
        ext = Path(filename or "photo.jpg").suffix or ".jpg"
        image_path = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"
        image_path.write_bytes(image_data)
        return image_path

    def _parse_response(self, content: str) -> PhotoRecognitionResult:
        """Parse GPT-4o response into structured result."""
        try:
            # Try to extract JSON from the response
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())

            return PhotoRecognitionResult(
                food_name=data.get("food_name", "Unknown food"),
                estimated_calories=float(data.get("estimated_calories", 0)),
                protein_g=float(data.get("protein_g", 0)),
                carbs_g=float(data.get("carbs_g", 0)),
                fat_g=float(data.get("fat_g", 0)),
                fiber_g=float(data.get("fiber_g", 0)),
                serving_size=data.get("serving_size"),
                confidence=float(data.get("confidence", 0.5)),
                notes=data.get("notes"),
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return PhotoRecognitionResult(
                food_name="Unrecognized food",
                estimated_calories=0,
                protein_g=0,
                carbs_g=0,
                fat_g=0,
                fiber_g=0,
                confidence=0.0,
                notes="Failed to parse AI response. Please log manually.",
            )

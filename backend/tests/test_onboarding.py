"""Tests for the profile_completed onboarding field."""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.user import User


class TestProfileCompleted:
    """Test the profile_completed computed field on GET /api/v1/users/me."""

    @pytest.mark.asyncio
    async def test_new_user_profile_not_completed(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A freshly registered user (no stats) should have profile_completed=false."""
        user = User(
            id=uuid.uuid4(),
            email="newuser@example.com",
            hashed_password=hash_password("testpass123"),
            name="New User",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(str(user.id))
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile_completed"] is False

    @pytest.mark.asyncio
    async def test_complete_profile_returns_true(
        self, client: AsyncClient, test_user: User, auth_headers: dict
    ):
        """The test_user fixture has all fields set, so profile_completed=true."""
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["profile_completed"] is True

    @pytest.mark.asyncio
    async def test_partial_profile_not_completed(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A user with only height and weight (missing age, sex) → profile_completed=false."""
        user = User(
            id=uuid.uuid4(),
            email="partial@example.com",
            hashed_password=hash_password("testpass123"),
            name="Partial User",
            height_cm=170,
            weight_kg=65,
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(str(user.id))
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile_completed"] is False

    @pytest.mark.asyncio
    async def test_completing_profile_via_put_flips_to_true(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Updating a bare user with all 4 required fields should flip profile_completed to true."""
        user = User(
            id=uuid.uuid4(),
            email="incomplete@example.com",
            hashed_password=hash_password("testpass123"),
            name="Incomplete User",
        )
        db_session.add(user)
        await db_session.commit()

        token = create_access_token(str(user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # Before update
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.json()["profile_completed"] is False

        # Complete the profile
        response = await client.put(
            "/api/v1/users/me",
            headers=headers,
            json={
                "height_cm": 180,
                "weight_kg": 75,
                "age": 25,
                "sex": "female",
                "activity_level": "moderately_active",
                "goal_type": "maintain",
            },
        )
        assert response.status_code == 200
        assert response.json()["profile_completed"] is True

    @pytest.mark.asyncio
    async def test_register_then_get_profile_not_completed(
        self, client: AsyncClient
    ):
        """After registration, GET /users/me should show profile_completed=false."""
        # Register
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "fresh@example.com",
                "password": "password123",
                "name": "Fresh User",
            },
        )
        assert reg.status_code == 201
        access_token = reg.json()["access_token"]

        # Fetch profile
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile_completed"] is False

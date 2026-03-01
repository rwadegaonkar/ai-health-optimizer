"""Tests for auth API endpoints."""

import pytest
from httpx import AsyncClient


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "password123", "name": "New User"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "testuser@example.com", "password": "password123", "name": "Dupe"},
        )
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "short", "name": "User"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123", "name": "User"},
        )
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert response.status_code == 401


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_valid_token(self, client: AsyncClient, test_user):
        # Login first to get a refresh token
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "testpass123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401


class TestProtectedEndpoints:
    @pytest.mark.asyncio
    async def test_profile_without_auth(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 403  # No bearer token

    @pytest.mark.asyncio
    async def test_profile_with_auth(self, client: AsyncClient, test_user, auth_headers):
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["name"] == "Test User"

"""Tests for core security utilities — password hashing and JWT tokens."""

from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_hash(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        hash1 = hash_password("mypassword")
        hash2 = hash_password("mypassword")
        assert hash1 != hash2  # bcrypt uses random salt


class TestJWTTokens:
    def test_create_access_token(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_access_token(self):
        token = create_access_token("user-123")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token("user-123")
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_empty_token(self):
        payload = decode_token("")
        assert payload is None

    def test_custom_expiry(self):
        token = create_access_token("user-123", expires_delta=timedelta(hours=1))
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"

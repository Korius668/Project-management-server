"""Integration tests for security utilities."""
import pytest
import jwt
from datetime import datetime, timedelta
from uuid import uuid4

from app.usecases.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id
)
from app.domain.exceptions import AuthenticationError
from app.config import secrets


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_hash(self):
        """Test that password hashing creates a hash."""
        password = "testpassword123"
        
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_hashes_for_same_password(self):
        """Test that same password creates different hashes (due to salt)."""
        password = "testpassword123"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2

    def test_verify_password_correct_password_returns_true(self):
        """Test that correct password verification returns True."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        result = verify_password(password, hashed)
        
        assert result is True

    def test_verify_password_incorrect_password_returns_false(self):
        """Test that incorrect password verification returns False."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        result = verify_password(wrong_password, hashed)
        
        assert result is False

    def test_verify_password_empty_password_returns_false(self):
        """Test that empty password verification returns False."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        result = verify_password("", hashed)
        
        assert result is False


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token_creates_valid_token(self):
        """Test that access token creation works."""
        user_id = uuid4()
        
        token = create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_user_id(self):
        """Test that created token contains user ID."""
        user_id = uuid4()
        
        token = create_access_token(user_id)
        
        # Decode token to verify contents
        payload = jwt.decode(token, secrets.secret_key, algorithms=[secrets.algorithm])
        assert payload["sub"] == str(user_id)

    def test_create_access_token_has_expiration(self):
        """Test that created token has expiration."""
        user_id = uuid4()
        
        token = create_access_token(user_id)
        
        # Decode token to verify expiration
        payload = jwt.decode(token, secrets.secret_key, algorithms=[secrets.algorithm])
        assert "exp" in payload
        
        # Expiration should be in the future
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        assert exp_datetime > datetime.now()



class TestCurrentUserExtraction:
    """Test current user ID extraction from token."""

    def test_get_current_user_id_valid_token_returns_uuid(self):
        """Test extracting user ID from valid token."""
        user_id = uuid4()
        token = create_access_token(user_id)
        
        result = get_current_user_id(token)
        
        assert result == user_id
        assert isinstance(result, type(user_id))

    def test_get_current_user_id_invalid_token_raises_http_exception(self):
        """Test that invalid token raises HTTP exception."""
        from fastapi import HTTPException
        
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in str(exc_info.value.detail)

    def test_get_current_user_id_expired_token_raises_http_exception(self):
        """Test that expired token raises HTTP exception."""
        from fastapi import HTTPException
        
        user_id = uuid4()
        
        # Create expired token
        past_time = datetime.now() - timedelta(minutes=50)
        payload = {
            "sub": str(user_id),
            "exp": int(past_time.timestamp())
        }
        expired_token = jwt.encode(payload, secrets.secret_key, algorithm=secrets.algorithm)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(expired_token)
        
        assert exc_info.value.status_code == 401

    def test_get_current_user_id_token_without_subject_raises_http_exception(self):
        """Test that token without subject raises HTTP exception."""
        from fastapi import HTTPException
        
        # Create token without 'sub' field
        payload = {
            "exp": datetime.now() + timedelta(minutes=30)
        }
        token_without_sub = jwt.encode(payload, secrets.secret_key, algorithm=secrets.algorithm)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(token_without_sub)
        
        assert exc_info.value.status_code == 401

    def test_get_current_user_id_invalid_uuid_raises_http_exception(self):
        """Test that invalid UUID in token raises HTTP exception."""
        from fastapi import HTTPException
        
        # Create token with invalid UUID
        payload = {
            "sub": "not-a-valid-uuid",
            "exp": datetime.now() + timedelta(minutes=30)
        }
        invalid_uuid_token = jwt.encode(payload, secrets.secret_key, algorithm=secrets.algorithm)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_id(invalid_uuid_token)
        
        assert exc_info.value.status_code == 401

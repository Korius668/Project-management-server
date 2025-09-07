import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.infrastructure.auth_middleware import get_current_user
from app.domain.models import User


class TestAuthMiddleware:
    def test_get_current_user_success(self, mock_session, sample_user):
        # Given
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        
        with patch('app.infrastructure.auth_middleware.get_user_id_from_token', return_value=123), \
             patch('app.infrastructure.auth_middleware.get_container') as mock_get_container:
            
            mock_container = Mock()
            mock_users_service = Mock()
            mock_users_service._repository.get_by_id.return_value = sample_user
            mock_container.users_service.return_value = mock_users_service
            mock_get_container.return_value = mock_container
            
            # When
            result = get_current_user(credentials, mock_session)
            
            # Then
            assert result == sample_user

    def test_get_current_user_not_found(self, mock_session):
        # Given
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
        
        with patch('app.infrastructure.auth_middleware.get_user_id_from_token', return_value=123), \
             patch('app.infrastructure.auth_middleware.get_container') as mock_get_container:
            
            mock_container = Mock()
            mock_users_service = Mock()
            mock_users_service._repository.get_by_id.return_value = None
            mock_container.users_service.return_value = mock_users_service
            mock_get_container.return_value = mock_container
            
            # When & Then
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(credentials, mock_session)
            
            assert exc_info.value.status_code == 401
            assert "User not found" in str(exc_info.value.detail)

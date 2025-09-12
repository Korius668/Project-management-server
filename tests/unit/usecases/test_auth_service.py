import pytest
from unittest.mock import Mock, patch
from datetime import timedelta
from uuid import uuid4

from app.usecases.auth import AuthService
from app.domain.exceptions import AuthenticationError
from app.domain.models import User


class TestAuthService:
    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def auth_service(self, mock_repository):
        return AuthService(mock_repository)

    @pytest.fixture
    def sample_user(self):
        return User(
            id=uuid4(),
            name="testuser",
            email="test@example.com",
            password_hash="hashed_password",
        )

    def test_create_user_success(self, auth_service, mock_repository):
        """Test successful user creation with password hashing."""
        # Arrange
        login = "newuser"
        password = "password123"
        email = "new@example.com"
        expected_user = User(
            id=uuid4(), name=login, email=email, password_hash="hashed_password"
        )

        with patch("app.usecases.auth.hash_password") as mock_hash:
            mock_hash.return_value = "hashed_password"
            mock_repository.create_user.return_value = expected_user

            # Act
            result = auth_service.create_user(login, password, email)

            # Assert
            mock_hash.assert_called_once_with(password)
            mock_repository.create_user.assert_called_once_with(
                login, "hashed_password", email
            )
            assert result == expected_user

    def test_login_success(self, auth_service, mock_repository, sample_user):
        """Test successful login with valid credentials."""
        # Arrange
        login = "testuser"
        password = "password123"
        expected_token = "jwt_token_here"

        mock_repository.get_user.return_value = sample_user

        with patch("app.usecases.auth.verify_password") as mock_verify, patch(
            "app.usecases.auth.create_access_token"
        ) as mock_create_token:
            mock_verify.return_value = True
            mock_create_token.return_value = expected_token

            # Act
            result = auth_service.login(login, password)

            # Assert
            mock_repository.get_user.assert_called_once_with(login)
            mock_verify.assert_called_once_with(password, sample_user.password_hash)
            mock_create_token.assert_called_once_with(sample_user.id)
            assert result == expected_token

    def test_login_user_not_found(self, auth_service, mock_repository):
        """Test login failure when user doesn't exist."""
        # Arrange
        login = "nonexistent"
        password = "password123"

        mock_repository.get_user.return_value = None

        # Act & Assert
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.login(login, password)

        mock_repository.get_user.assert_called_once_with(login)

    def test_login_invalid_password(self, auth_service, mock_repository, sample_user):
        """Test login failure with invalid password."""
        # Arrange
        login = "testuser"
        password = "wrong_password"

        mock_repository.get_user.return_value = sample_user

        with patch("app.usecases.auth.verify_password") as mock_verify:
            mock_verify.return_value = False

            # Act & Assert
            with pytest.raises(AuthenticationError, match="Invalid email or password"):
                auth_service.login(login, password)

            mock_repository.get_user.assert_called_once_with(login)
            mock_verify.assert_called_once_with(password, sample_user.password_hash)

    def test_auth_service_initialization(self, mock_repository):
        """Test AuthService initialization with repository."""
        # Act
        service = AuthService(mock_repository)

        # Assert
        assert service.repository == mock_repository

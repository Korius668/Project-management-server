import pytest
from app.domain.exceptions import  AuthenticationError
from unittest.mock import patch

from app.usecases.auth import UsersService


@pytest.fixture
def service(mock_repo):
    return UsersService(mock_repo)

@pytest.fixture(scope="module")
def user1():
    login = "user_1"
    password = "VerySafePass123"
    email = "user1@gugu.com"
    return login, password, email

class TestCreateUser:
    def test_correct_input(self, user1, mock_repo, service):
        login, password, email = user1
        result = service.create_user(login, password, email)
        mock_repo.add.assert_called_once()
        assert result.name == login
        assert result.email == email
        assert result.password_hash != password


class TestLogin:
    def test_login_existing_user(self, user1, mock_repo, service, new_user):
        login, password, email = user1
        mock_repo.get_by_name.return_value = new_user
        token = service.login(login, password)
        mock_repo.get_by_name.assert_called_once()
        assert isinstance(token, str)
        assert len(token) > 10

    def test_login_success(self, service, mock_repo, sample_user):
        mock_repo.get_by_name.return_value = sample_user

        with patch(
            "app.usecases.auth.verify_password", return_value=True
        ) as mock_verify, patch(
            "app.usecases.auth.create_access_token", return_value="faketoken"
        ) as mock_token:
            token = service.login("testuser", "plainpass")

            mock_repo.get_by_name.assert_called_once_with("testuser")
            mock_verify.assert_called_once_with("plainpass", sample_user.password_hash)
            mock_token.assert_called_once()
            assert token == "faketoken"

    def test_login_user_not_found(self, service, mock_repo):
        mock_repo.get_by_name.return_value = None

        with patch("app.usecases.auth.verify_password") as mock_verify:
            with pytest.raises(AuthenticationError) as exc:
                service.login("nonexistent", "pass")
            assert "Invalid email or password" in str(exc.value)
            mock_verify.assert_not_called()

    def test_login_invalid_password(self, service, mock_repo, sample_user):
        mock_repo.get_by_name.return_value = sample_user

        with patch(
            "app.usecases.auth.verify_password", return_value=False
        ) as mock_verify:
            with pytest.raises(AuthenticationError) as exc:
                service.login("testuser", "wrongpass")
            assert "Invalid email or password" in str(exc.value)
            mock_verify.assert_called_once_with("wrongpass", sample_user.password_hash)

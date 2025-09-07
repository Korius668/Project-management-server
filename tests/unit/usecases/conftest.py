from unittest.mock import Mock
import pytest
from uuid import uuid4

from app.domain.models import User


@pytest.fixture(scope="module")
def user1():
    login = "user_1"
    password ="VerySafePass123"
    email = "user1@gugu.com"
    return login, password, email

@pytest.fixture()
def mock_repo():
    return Mock()

@pytest.fixture
def new_user(user1, service):
    login, password, email = user1
    return service.create_user(login, password, email)

@pytest.fixture
def sample_user():
    return User(
        id=uuid4(),
        email="test@example.com",
        name="testuser",
        password_hash="hashedpass"
    )

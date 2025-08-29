import pytest
from unittest.mock import patch
from uuid import uuid4
from app.domain.models import User


@pytest.fixture
def mock_repo():
    with patch(
        "app.adapters.sqlalchemy.repositories.SqlAlchemyUsersRepository"
    ) as mock_repo:

        yield mock_repo


def test_add_and_get_user(mock_repo):
    repo = mock_repo.return_value
    user = User(
        id=uuid4(), email="test@example.com", name="Test User", password_hash="hashed"
    )

    repo.add(user)
    fetched = repo.get(user.id)

    fetched.configure_mock(email="test@example.com", name="Test User")

    assert fetched is not None
    assert fetched.email == "test@example.com"
    assert fetched.name == "Test User"
    mock_repo.return_value.add.assert_called_once_with(user)
    mock_repo.return_value.get.assert_called_once_with(user.id)


def test_list_users(mock_repo):
    repo = mock_repo.return_value
    user1 = User(id=uuid4(), email="u1@example.com", name="User1", password_hash="x")
    user2 = User(id=uuid4(), email="u2@example.com", name="User2", password_hash="y")

    repo.list.return_value = [user1, user2]

    repo.add(user1)
    repo.add(user2)

    users = repo.list()
    assert len(users) == 2
    emails = [u.email for u in users]
    assert "u1@example.com" in emails
    assert "u2@example.com" in emails
    mock_repo.return_value.add.assert_any_call(user1)
    mock_repo.return_value.add.assert_any_call(user2)
    mock_repo.return_value.list.assert_called_once()

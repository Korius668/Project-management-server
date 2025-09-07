import pytest
from unittest.mock import Mock
from uuid import uuid4
from app.adapters.sqlalchemy.repositories import SqlAlchemyUsersRepository
from app.adapters.sqlalchemy.models import UserORM
from app.domain.models import User


@pytest.fixture
def mock_query_chain(mock_session):
    """Pomocniczy fixture do chainowania query()"""
    mock_query = Mock()
    mock_filter = Mock()
    mock_query.filter_by.return_value = mock_filter
    mock_session.query.return_value = mock_query
    return mock_query, mock_filter


@pytest.fixture
def repo(mock_session):
    return SqlAlchemyUsersRepository(mock_session)


class TestSqlAlchemyUsersRepository:

    def test_add_user_success(self, sample_user, mock_session, repo):
        # When
        result = repo.add(sample_user)
        # Then
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result == sample_user
        # Verify ORM object was created correctly
        orm_call = mock_session.add.call_args[0][0]
        assert isinstance(orm_call, UserORM)
        assert orm_call.id == sample_user.id
        assert orm_call.email == sample_user.email
        assert orm_call.name == sample_user.name
        assert orm_call.password_hash == sample_user.password_hash

    def test_get_user_found(self, sample_user, mock_session, repo):
        # Mock ORM object
        mock_orm = Mock(spec=UserORM)
        mock_orm.id = sample_user.id
        mock_orm.email = sample_user.email
        mock_orm.name = sample_user.name
        mock_orm.password_hash = sample_user.password_hash

        mock_session.get.return_value = mock_orm
        repo = SqlAlchemyUsersRepository(mock_session)
        # When
        result = repo.get(sample_user.id)
        # Then
        mock_session.get.assert_called_once_with(UserORM, sample_user.id)
        assert result is not None
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.name == sample_user.name

    def test_get_user_not_found(self, sample_user, mock_session, repo):
        # Given
        mock_session.get.return_value = None
        # When
        result = repo.get(sample_user.id)
        # Then
        mock_session.get.assert_called_once_with(UserORM, sample_user.id)
        assert result is None

    def test_list_users(self, mock_session, repo):

        # Mock ORM objects
        mock_orms = []
        for i in range(3):
            mock_orm = Mock(spec=UserORM)
            mock_orm.id = uuid4()
            mock_orm.email = f"user{i}@example.com"
            mock_orm.name = f"User {i}"
            mock_orm.password_hash = "hashed"
            mock_orms.append(mock_orm)

        mock_query = Mock()
        mock_query.all.return_value = mock_orms
        mock_session.query.return_value = mock_query

        repo = SqlAlchemyUsersRepository(mock_session)

        # When
        result = repo.list()

        # Then
        mock_session.query.assert_called_once_with(UserORM)
        mock_query.all.assert_called_once()
        assert len(result) == 3
        assert all(isinstance(user, User) for user in result)
        assert result[0].email == "user0@example.com"
        assert result[1].email == "user1@example.com"
        assert result[2].email == "user2@example.com"

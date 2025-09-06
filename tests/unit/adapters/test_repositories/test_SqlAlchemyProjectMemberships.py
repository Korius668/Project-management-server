import pytest
from unittest.mock import Mock
from uuid import uuid4

from app.adapters.sqlalchemy.repositories import (
    SqlAlchemyProjectMembershipsRepository,
)
from app.adapters.sqlalchemy.models import (
    ProjectMembershipORM,
)
from app.domain.models import ProjectMembership, ProjectRole


@pytest.fixture
def mock_session():
    return Mock()


@pytest.fixture
def repo(mock_session):
    return SqlAlchemyProjectMembershipsRepository(mock_session)


@pytest.fixture
def sample_membership():
    return ProjectMembership(project_id=uuid4(), user_id=uuid4(), role="editor")


@pytest.fixture
def mock_query_chain(mock_session):
    """Pomocniczy fixture do chainowania query()"""
    mock_query = Mock()
    mock_filter = Mock()
    mock_query.filter_by.return_value = mock_filter
    mock_session.query.return_value = mock_query
    return mock_query, mock_filter


class TestAddMembership:
    def test_add_success(self, sample_membership, mock_session, repo):
        mock_session.merge.return_value = Mock()

        result = repo.add(sample_membership)

        mock_session.merge.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result == sample_membership
        orm_call = mock_session.merge.call_args[0][0]
        assert isinstance(orm_call, ProjectMembershipORM)
        assert orm_call.project_id == sample_membership.project_id
        assert orm_call.user_id == sample_membership.user_id
        assert orm_call.role == sample_membership.role


class TestGetMembership:
    def test_existing(self, sample_membership, mock_query_chain, repo):
        _, mock_filter = mock_query_chain
        orm_instance = Mock()
        mock_filter.first.return_value = orm_instance
        ProjectMembership.model_validate = Mock(return_value=sample_membership)

        result = repo.get(sample_membership.project_id, sample_membership.user_id)

        mock_filter.first.assert_called_once()
        ProjectMembership.model_validate.assert_called_once_with(
            orm_instance, from_attributes=True
        )
        assert result == sample_membership

    def test_missing(self, sample_membership, mock_query_chain, repo):
        _, mock_filter = mock_query_chain
        mock_filter.first.return_value = None

        result = repo.get(sample_membership.project_id, sample_membership.user_id)

        assert result is None


class TestUpdateMembership:
    def test_existing(self, sample_membership, mock_query_chain, repo):
        _, mock_filter = mock_query_chain
        orm_instance = Mock()
        mock_filter.first.return_value = orm_instance

        result = repo.update(sample_membership)

        assert orm_instance.role == sample_membership.role
        repo.session.commit.assert_called_once()
        assert result == sample_membership

    def test_missing(self, sample_membership, mock_query_chain, repo):
        _, mock_filter = mock_query_chain
        mock_filter.first.return_value = None

        result = repo.update(sample_membership)

        assert result is None
        repo.session.commit.assert_not_called()


class TestListMemberships:
    def test_list_all(self, repo, mock_session):
        orm1, orm2 = Mock(), Mock()
        mock_session.query.return_value.all.return_value = [orm1, orm2]
        ProjectMembership.model_validate = Mock(side_effect=["m1", "m2"])

        result = repo.list()

        assert result == ["m1", "m2"]
        mock_session.query.assert_called_once_with(ProjectMembershipORM)

    def test_list_by_project(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        orm_list = [Mock(), Mock()]
        mock_filter.all.return_value = orm_list
        ProjectMembership.model_validate = Mock(side_effect=["m1", "m2"])

        result = repo.list_by_project("proj-id")

        assert result == ["m1", "m2"]
        mock_filter.all.assert_called_once()

    def test_list_by_user(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        orm_list = [Mock()]
        mock_filter.all.return_value = orm_list
        ProjectMembership.model_validate = Mock(return_value="m1")

        result = repo.list_by_user("user-id")

        assert result == ["m1"]
        mock_filter.all.assert_called_once()


class TestDeleteMemberships:
    def test_delete_one(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        mock_filter.delete.return_value = 1

        result = repo.delete("proj", "user")

        repo.session.commit.assert_called_once()
        assert result is True

    def test_delete_one_not_found(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        mock_filter.delete.return_value = 0

        result = repo.delete("proj", "user")

        assert result is False

    def test_delete_by_project(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        mock_filter.delete.return_value = 5

        result = repo.delete_by_project("proj")

        assert result == 5
        repo.session.commit.assert_called_once()

    def test_delete_by_user(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        mock_filter.delete.return_value = 3

        result = repo.delete_by_user("usr")

        assert result == 3
        repo.session.commit.assert_called_once()


class TestExistsMembership:
    def test_exists_true(self, repo, mock_session):
        inner_query = Mock()
        mock_session.query.return_value = inner_query
        inner_query.scalar.return_value = True

        result = repo.exists("proj", "user")

        assert result is True

    def test_exists_false(self, repo, mock_session):
        inner_query = Mock()
        mock_session.query.return_value = inner_query
        inner_query.scalar.return_value = False

        result = repo.exists("proj", "user")

        assert result is False


class TestCountByProject:
    def test_count(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        mock_filter.count.return_value = 42

        result = repo.count_by_project("proj")

        assert result == 42


class TestGetUserRole:
    def test_existing(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        orm_instance = Mock(role="owner")
        mock_filter.first.return_value = orm_instance
        ProjectRoleClass = ProjectRole

        result = repo.get_user_role("proj", "user")

        assert isinstance(result, ProjectRoleClass)
        assert result.value == "owner"

    def test_missing(self, repo, mock_query_chain):
        _, mock_filter = mock_query_chain
        mock_filter.first.return_value = None

        result = repo.get_user_role("proj", "user")

        assert result is None

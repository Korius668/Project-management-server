import pytest
from unittest.mock import Mock
from uuid import uuid4

from app.usecases.projects import ProjectsService
from app.domain.models import ProjectMembership, ProjectRole
from app.domain.exceptions import (
    ProjectNotFoundError,
    UserNotFoundError,
    InsufficientPermissionsError,
    UserAlreadyMemberError,
    PermissionDeniedError,
)
from app.api.schemas.responses import (
    ProjectResponse,
    ProjectInfoResponse,
    ProjectListResponse,
)


@pytest.fixture
def service(
    mock_projects_repository,
    mock_users_repository,
    mock_memberships_repository,
    mock_documents_repository,
    mock_file_storage,
):
    """ProjectsService instance with mocked dependencies"""
    return ProjectsService(
        mock_projects_repository,
        mock_users_repository,
        mock_memberships_repository,
        mock_documents_repository,
        mock_file_storage,
    )


class TestCreateProject:
    def test_success(
        self,
        mock_projects_repository,
        mock_users_repository,
        mock_memberships_repository,
        user1,
        sample_project,
        service,
    ):
        # Given
        mock_users_repository.get.return_value = user1
        mock_projects_repository.add.return_value = sample_project
        mock_memberships_repository.add.return_value = Mock()

        # When
        result = service.create_project("Test Project", "Description", user1.id)

        # Then
        assert isinstance(result, ProjectResponse)
        assert result.name == "Test Project"
        mock_users_repository.get.assert_called_once_with(user1.id)
        mock_projects_repository.add.assert_called_once()
        mock_memberships_repository.add.assert_called_once()

    def test_user_not_found(self, mock_users_repository, service):
        # Given
        mock_users_repository.get.return_value = None
        user_id = uuid4()

        # When & Then
        with pytest.raises(UserNotFoundError):
            service.create_project("Test Project", "Description", user_id)


class TestGetProject:

    def test_success(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        sample_membership,
        service,
    ):
        # Given
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = sample_membership

        # When
        result = service.get_project(sample_project.id, sample_membership.user_id)

        # Then
        assert isinstance(result, ProjectResponse)
        assert result.id == str(sample_project.id)
        mock_projects_repository.get.assert_called_once_with(sample_project.id)

    def test_not_found(self, mock_projects_repository, service):
        # Given
        mock_projects_repository.get.return_value = None
        project_id = uuid4()
        user_id = uuid4()

        # When & Then
        with pytest.raises(ProjectNotFoundError):
            service.get_project(project_id, user_id)

    def test_no_permission(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = None
        user_id = uuid4()

        # When & Then
        with pytest.raises(PermissionDeniedError):
            service.get_project(sample_project.id, user_id)


class TestGetProjectInfo:
    def test_success(
        self,
        mock_projects_repository,
        mock_users_repository,
        mock_memberships_repository,
        mock_documents_repository,
        user1,
        project1,
        document1,
        membership1,
        service,
    ):
        # Given

        mock_projects_repository.get.return_value = project1
        mock_memberships_repository.get.return_value = membership1
        mock_users_repository.get.return_value = user1
        mock_memberships_repository.list_by_project.return_value = [membership1]
        mock_documents_repository.list_by_project.return_value = [document1]

        # When
        result = service.get_project_info(project1.id, user1.id)

        # Then
        assert isinstance(result, ProjectInfoResponse)
        assert result.project.id == str(project1.id)
        assert len(result.members) == 1
        assert len(result.documents) == 1


class TestUpdateProject:
    def test_success(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(
            project_id=sample_project.id, user_id=user_id, role=ProjectRole.editor
        )
        mock_projects_repository.update.return_value = sample_project

        # When
        result = service.update_project(
            sample_project.id, user_id, "New Name", "New Description"
        )

        # Then
        assert isinstance(result, ProjectResponse)
        assert result.name == "New Name"
        mock_projects_repository.update.assert_called_once()

    def test_denied(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(
            project_id=sample_project.id, user_id=user_id, role=ProjectRole.viewer
        )

        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.update_project(sample_project.id, user_id, "New Name")


class TestDeleteProject:

    def test_success(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given

        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(
            project_id=sample_project.id, user_id=user_id, role=ProjectRole.owner
        )
        mock_memberships_repository.delete_by_project.return_value = 1
        mock_projects_repository.delete.return_value = None

        # When
        result = service.delete_project(sample_project.id, user_id)

        # Then
        assert result is None
        mock_projects_repository.delete.assert_called_once_with(sample_project.id)

    def test_non_owner_denied(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(
            project_id=sample_project.id, user_id=user_id, role=ProjectRole.viewer
        )

        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.delete_project(sample_project.id, user_id)


class TestInviteUserToProject:

    def test_success(
        self,
        mock_projects_repository,
        mock_users_repository,
        mock_memberships_repository,
        user1,
        another_user,
        sample_project,
        sample_membership,
        service,
    ):
        # Given
        invited_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=another_user.id,
            role=ProjectRole.editor,
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [sample_membership, None]
        mock_users_repository.get.return_value = another_user
        mock_memberships_repository.add.return_value = invited_membership

        # When
        result = service.invite_user_to_project(
            sample_project.id, user1.id, another_user.id, ProjectRole.editor
        )

        # Then
        assert isinstance(result, ProjectMembership)
        assert result.role == ProjectRole.editor
        mock_memberships_repository.add.assert_called_once()

    def test_user_already_member(
        self,
        mock_projects_repository,
        mock_users_repository,
        mock_memberships_repository,
        user1,
        another_user,
        sample_project,
        sample_membership,
        editor_membership,
        service,
    ):
        # Given
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [
            sample_membership,
            editor_membership,
        ]
        mock_users_repository.get.return_value = another_user

        # When & Then
        with pytest.raises(UserAlreadyMemberError):
            service.invite_user_to_project(
                sample_project.id, user1.id, another_user.id, ProjectRole.editor
            )


class TestGetUserProjects:
    def test_success(
        self,
        mock_users_repository,
        mock_memberships_repository,
        mock_projects_repository,
        user1,
        sample_project,
        service,
    ):
        # Given
        membership = ProjectMembership(
            project_id=sample_project.id, user_id=user1.id, role=ProjectRole.editor
        )
        mock_users_repository.get.return_value = user1
        mock_memberships_repository.list_by_user.return_value = [membership]
        mock_projects_repository.get.return_value = sample_project

        # When
        result = service.get_user_projects(user1.id)

        # Then
        assert isinstance(result, ProjectListResponse)
        assert len(result.projects) == 1
        assert result.projects[0].id == str(sample_project.id)
        mock_users_repository.get.assert_called_once_with(user1.id)
        mock_memberships_repository.list_by_user.assert_called_once_with(user1.id)

    def test_user_not_found(self, mock_users_repository, service):
        # Given
        user_id = uuid4()
        mock_users_repository.get.return_value = None

        # When & Then
        with pytest.raises(UserNotFoundError):
            service.get_user_projects(user_id)

    def test_empty_list(
        self, mock_users_repository, mock_memberships_repository, user1, service
    ):
        # Given
        mock_users_repository.get.return_value = user1
        mock_memberships_repository.list_by_user.return_value = []

        # When
        result = service.get_user_projects(user1.id)

        # Then
        assert isinstance(result, ProjectListResponse)
        assert result.projects == []


class TestUpdateUserRole:
    def test_success(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id, user_id=updater_id, role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=target_user_id,
            role=ProjectRole.viewer,
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [
            updater_membership,
            target_membership,
        ]
        mock_memberships_repository.update.return_value = target_membership

        # When
        result = service.update_user_role(
            sample_project.id, updater_id, target_user_id, ProjectRole.editor
        )

        # Then
        assert result == target_membership
        mock_memberships_repository.update.assert_called_once()

    def test_not_owner(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id, user_id=updater_id, role=ProjectRole.editor
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = updater_membership

        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.update_user_role(
                sample_project.id, updater_id, target_user_id, ProjectRole.editor
            )

    def test_target_not_member(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id, user_id=updater_id, role=ProjectRole.owner
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [updater_membership, None]

        # When & Then
        with pytest.raises(UserNotFoundError):
            service.update_user_role(
                sample_project.id, updater_id, target_user_id, ProjectRole.editor
            )

    def test_cannot_change_owner(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id, user_id=updater_id, role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id, user_id=target_user_id, role=ProjectRole.owner
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [
            updater_membership,
            target_membership,
        ]

        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.update_user_role(
                sample_project.id, updater_id, target_user_id, ProjectRole.editor
            )


class TestRemoveUserFromProject:
    def test_success(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id, user_id=remover_id, role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=target_user_id,
            role=ProjectRole.editor,
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [
            remover_membership,
            target_membership,
        ]
        mock_memberships_repository.delete.return_value = True

        # When
        result = service.remove_user_from_project(
            sample_project.id, remover_id, target_user_id
        )

        # Then
        assert result is True
        mock_memberships_repository.delete.assert_called_once_with(
            sample_project.id, target_user_id
        )

    def test_no_permission(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id, user_id=remover_id, role=ProjectRole.viewer
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = remover_membership

        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.remove_user_from_project(
                sample_project.id, remover_id, target_user_id
            )

    def test_target_not_member(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id, user_id=remover_id, role=ProjectRole.owner
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [remover_membership, None]

        # When & Then
        with pytest.raises(UserNotFoundError):
            service.remove_user_from_project(
                sample_project.id, remover_id, target_user_id
            )

    def test_cannot_remove_owner(
        self,
        mock_projects_repository,
        mock_memberships_repository,
        sample_project,
        service,
    ):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id, user_id=remover_id, role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id, user_id=target_user_id, role=ProjectRole.owner
        )

        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [
            remover_membership,
            target_membership,
        ]

        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.remove_user_from_project(
                sample_project.id, remover_id, target_user_id
            )

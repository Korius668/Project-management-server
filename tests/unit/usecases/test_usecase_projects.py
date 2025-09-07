import pytest
from unittest.mock import Mock
from uuid import uuid4

from app.usecases.projects import ProjectsService
from app.domain.models import Project, ProjectMembership, ProjectRole
from app.domain.exceptions import (
    ProjectNotFoundError, 
    UserNotFoundError, 
    PermissionDeniedError,
    UserAlreadyMemberError,
    InsufficientPermissionsError
)

@pytest.fixture
def service(mock_projects_repository, mock_users_repository, mock_memberships_repository):
    return ProjectsService(mock_projects_repository, mock_users_repository, mock_memberships_repository)


class TestCreateProject:
    def test_create_project_success(self, mock_projects_repository, mock_users_repository, mock_memberships_repository, sample_user, sample_project, service):
        # Given
        mock_users_repository.get.return_value = sample_user
        mock_projects_repository.add.return_value = sample_project
        mock_memberships_repository.add.return_value = Mock()
        
        # When
        result = service.create_project("Test Project", "Description", sample_user.id)
        
        # Then
        assert result.name == "Test Project"
        mock_users_repository.get.assert_called_once_with(sample_user.id)
        mock_projects_repository.add.assert_called_once()
        mock_memberships_repository.add.assert_called_once()

    def test_create_project_user_not_found(self, mock_users_repository, service):
        # Given
        mock_users_repository.get.return_value = None
        user_id = uuid4()
        
        # When & Then
        with pytest.raises(UserNotFoundError):
            service.create_project("Test Project", "Description", user_id)

class TestGetProject:
    def test_get_project_success(self, mock_projects_repository, mock_memberships_repository, sample_project, sample_membership, service):
        # Given
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = sample_membership
        
        # When
        result = service.get_project(sample_project.id, sample_membership.user_id)
        
        # Then
        assert result == sample_project
        mock_projects_repository.get.assert_called_once_with(sample_project.id)

    def test_get_project_not_found(self, mock_projects_repository, service):
        # Given
        mock_projects_repository.get.return_value = None
        project_id = uuid4()
        user_id = uuid4()
        
        # When & Then
        with pytest.raises(ProjectNotFoundError):
            service.get_project(project_id, user_id)

    def test_get_project_no_permission(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = None
        user_id = uuid4()
        
        # When & Then
        with pytest.raises(PermissionDeniedError):
            service.get_project(sample_project.id, user_id)


class TestUpdateProject:
    def test_update_project_success(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(project_id = sample_project.id, user_id = user_id, role = ProjectRole.editor)
        mock_projects_repository.update.return_value = sample_project
        
        # When
        result = service.update_project(sample_project.id, user_id, "New Name", "New Description")
        
        # Then
        assert result == sample_project
        mock_projects_repository.update.assert_called_once()

    def test_update_project_viewer_permission_denied(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(project_id = sample_project.id, user_id = user_id, role = ProjectRole.viewer)
        
        # When & Then
        with pytest.raises(PermissionDeniedError):
            service.update_project(sample_project.id, user_id, "New Name")


class TestDeleteProject:

    def test_delete_project_success(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        
        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(project_id = sample_project.id, user_id = user_id, role = ProjectRole.owner)
        mock_projects_repository.delete.return_value = None
        
        # When
        result = service.delete_project(sample_project.id, user_id)
        
        # Then
        assert result is None
        mock_projects_repository.delete.assert_called_once_with(sample_project.id)

    def test_delete_project_non_owner_denied(self, mock_projects_repository, mock_users_repository, mock_memberships_repository, sample_project, service):
        # Given
        service = ProjectsService(mock_projects_repository, mock_users_repository, mock_memberships_repository)
        user_id = uuid4()
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = ProjectMembership(project_id = sample_project.id, user_id = user_id, role = ProjectRole.viewer)
        
        # When & Then
        with pytest.raises(PermissionDeniedError):
            service.delete_project(sample_project.id, user_id)


class TestInviteUserToProject:

    def test_invite_user_success(self, mock_projects_repository, mock_users_repository, mock_memberships_repository, sample_project, sample_user, service):
        # Given
        inviter_id = sample_project.owner_id
        old_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=inviter_id,
            role=ProjectRole.owner
        )
        new_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role=ProjectRole.editor
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [old_membership, None]  # inviter is owner, invited user not member
        mock_users_repository.get.return_value = sample_user
        mock_memberships_repository.add.return_value = new_membership
        
        # When
        result = service.invite_user_to_project(
            sample_project.id, 
            inviter_id, 
            sample_user.id, 
            ProjectRole.editor
        )
        
        # Then
        assert result == new_membership
        mock_memberships_repository.add.assert_called_once()

    def test_invite_user_already_member(self, mock_projects_repository, mock_users_repository, mock_memberships_repository, sample_project, sample_user, service):
        # Given
        inviter_id = uuid4()
        old_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=inviter_id,
            role=ProjectRole.owner
        )
        new_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=sample_user.id,
            role=ProjectRole.viewer
        )
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [old_membership, new_membership]  # inviter is owner, user already member
        mock_users_repository.get.return_value = sample_user
        
        # When & Then
        with pytest.raises(UserAlreadyMemberError):
            service.invite_user_to_project(
                sample_project.id, 
                inviter_id, 
                sample_user.id, 
                ProjectRole.editor
            )

class TestUpdateUserRole:
    def test_update_user_role_success(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=updater_id,
            role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=target_user_id,
            role=ProjectRole.viewer
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [updater_membership, target_membership]
        mock_memberships_repository.update.return_value = target_membership
        
        # When
        result = service.update_user_role(sample_project.id, updater_id, target_user_id, ProjectRole.editor)
        
        # Then
        assert result == target_membership
        mock_memberships_repository.update.assert_called_once()

    def test_update_user_role_not_owner(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=updater_id,
            role=ProjectRole.editor
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = updater_membership
        
        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.update_user_role(sample_project.id, updater_id, target_user_id, ProjectRole.editor)

    def test_update_user_role_target_not_member(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=updater_id,
            role=ProjectRole.owner
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [updater_membership, None]
        
        # When & Then
        with pytest.raises(UserNotFoundError):
            service.update_user_role(sample_project.id, updater_id, target_user_id, ProjectRole.editor)

    def test_update_user_role_cannot_change_owner(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        updater_id = uuid4()
        target_user_id = uuid4()
        updater_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=updater_id,
            role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=target_user_id,
            role=ProjectRole.owner
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [updater_membership, target_membership]
        
        # When & Then
        with pytest.raises(PermissionDeniedError):
            service.update_user_role(sample_project.id, updater_id, target_user_id, ProjectRole.editor)


class TestRemoveUserFromProject:
    def test_remove_user_from_project_success(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=remover_id,
            role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=target_user_id,
            role=ProjectRole.editor
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [remover_membership, target_membership]
        mock_memberships_repository.delete.return_value = True
        
        # When
        result = service.remove_user_from_project(sample_project.id, remover_id, target_user_id)
        
        # Then
        assert result is True
        mock_memberships_repository.delete.assert_called_once_with(sample_project.id, target_user_id)

    def test_remove_user_from_project_no_permission(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=remover_id,
            role=ProjectRole.viewer
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.return_value = remover_membership
        
        # When & Then
        with pytest.raises(InsufficientPermissionsError):
            service.remove_user_from_project(sample_project.id, remover_id, target_user_id)

    def test_remove_user_from_project_target_not_member(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=remover_id,
            role=ProjectRole.owner
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [remover_membership, None]
        
        # When & Then
        with pytest.raises(UserNotFoundError):
            service.remove_user_from_project(sample_project.id, remover_id, target_user_id)

    def test_remove_user_from_project_cannot_remove_owner(self, mock_projects_repository, mock_memberships_repository, sample_project, service):
        # Given
        remover_id = uuid4()
        target_user_id = uuid4()
        remover_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=remover_id,
            role=ProjectRole.owner
        )
        target_membership = ProjectMembership(
            project_id=sample_project.id,
            user_id=target_user_id,
            role=ProjectRole.owner
        )
        
        mock_projects_repository.get.return_value = sample_project
        mock_memberships_repository.get.side_effect = [remover_membership, target_membership]
        
        # When & Then
        with pytest.raises(PermissionDeniedError):
            service.remove_user_from_project(sample_project.id, remover_id, target_user_id)
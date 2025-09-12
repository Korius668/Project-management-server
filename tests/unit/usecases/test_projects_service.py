import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from typing import List
from fastapi import UploadFile

from app.usecases.projects import ProjectsService
from app.domain.models import Project, ProjectMembership, ProjectRole, Document


class TestProjectsService:
    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def projects_service(self, mock_repository):
        return ProjectsService(mock_repository)

    @pytest.fixture
    def sample_project(self):
        return Project(
            id=uuid4(),
            name="Test Project",
            description="Test description",
            owner_id=uuid4()
        )

    @pytest.fixture
    def sample_membership(self):
        return ProjectMembership(
            id=uuid4(),
            project_id=uuid4(),
            user_id=uuid4(),
            role=ProjectRole.viewer
        )

    @pytest.fixture
    def mock_upload_files(self):
        files = []
        for i in range(2):
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = f"test{i}.pdf"
            mock_file.content_type = "application/pdf"
            files.append(mock_file)
        return files

    def test_create_project_success(self, projects_service, mock_repository, sample_project):
        """Test successful project creation."""
        # Arrange
        name = "New Project"
        description = "New project description"
        owner_id = uuid4()
        
        mock_repository.create_project.return_value = sample_project
        
        # Act
        result = projects_service.create_project(name, description, owner_id)
        
        # Assert
        mock_repository.create_project.assert_called_once_with(name, description, owner_id)
        assert result == sample_project

    def test_get_project_success(self, projects_service, mock_repository, sample_project):
        """Test successful project retrieval."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        
        mock_repository.get_project.return_value = sample_project
        
        # Act
        result = projects_service.get_project(project_id, user_id)
        
        # Assert
        mock_repository.get_project.assert_called_once_with(project_id, user_id)
        assert result == sample_project

    def test_get_user_projects_success(self, projects_service, mock_repository):
        """Test successful retrieval of user projects."""
        # Arrange
        user_id = uuid4()
        projects = [
            Project(id=uuid4(), name="Project 1", description="Desc 1", owner_id=user_id),
            Project(id=uuid4(), name="Project 2", description="Desc 2", owner_id=user_id)
        ]
        
        mock_repository.get_user_projects.return_value = projects
        
        # Act
        result = projects_service.get_user_projects(user_id)
        
        # Assert
        mock_repository.get_user_projects.assert_called_once_with(user_id)
        assert result == projects
        assert len(result) == 2

    def test_update_project_success(self, projects_service, mock_repository, sample_project):
        """Test successful project update."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        name = "Updated Project"
        description = "Updated description"
        
        mock_repository.update_project.return_value = sample_project
        
        # Act
        result = projects_service.update_project(project_id, user_id, name, description)
        
        # Assert
        mock_repository.update_project.assert_called_once_with(
            project_id, user_id, name, description
        )
        assert result == sample_project

    def test_update_project_partial(self, projects_service, mock_repository, sample_project):
        """Test project update with only name."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        name = "New Name Only"
        
        mock_repository.update_project.return_value = sample_project
        
        # Act
        result = projects_service.update_project(project_id, user_id, name=name)
        
        # Assert
        mock_repository.update_project.assert_called_once_with(
            project_id, user_id, name, None
        )
        assert result == sample_project

    def test_delete_project_success(self, projects_service, mock_repository):
        """Test successful project deletion."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        
        mock_repository.delete_project.return_value = None
        
        # Act
        result = projects_service.delete_project(project_id, user_id)
        
        # Assert
        mock_repository.delete_project.assert_called_once_with(project_id, user_id)


    def test_invite_user_to_project_success(self, projects_service, mock_repository, sample_membership):
        """Test successful user invitation to project."""
        # Arrange
        project_id = uuid4()
        inviter_id = uuid4()
        invited_user_id = uuid4()
        role = ProjectRole.editor
        
        mock_repository.invite_user_to_project.return_value = sample_membership
        
        # Act
        result = projects_service.invite_user_to_project(
            project_id, inviter_id, invited_user_id, role
        )
        
        # Assert
        mock_repository.invite_user_to_project.assert_called_once_with(
            project_id, inviter_id, invited_user_id, role
        )
        assert result == sample_membership

    def test_update_user_role_success(self, projects_service, mock_repository, sample_membership):
        """Test successful user role update."""
        # Arrange
        project_id = uuid4()
        updater_id = uuid4()
        target_user_id = uuid4()
        new_role = ProjectRole.owner
        
        mock_repository.update_user_role.return_value = sample_membership
        
        # Act
        result = projects_service.update_user_role(
            project_id, updater_id, target_user_id, new_role
        )
        
        # Assert
        mock_repository.update_user_role.assert_called_once_with(
            project_id, updater_id, target_user_id, new_role
        )
        assert result == sample_membership

    def test_remove_user_from_project_success(self, projects_service, mock_repository):
        """Test successful user removal from project."""
        # Arrange
        project_id = uuid4()
        remover_id = uuid4()
        target_user_id = uuid4()
        
        mock_repository.remove_user_from_project.return_value = True
        
        # Act
        result = projects_service.remove_user_from_project(
            project_id, remover_id, target_user_id
        )
        
        # Assert
        mock_repository.remove_user_from_project.assert_called_once_with(
            project_id, remover_id, target_user_id
        )
        assert result is True

    def test_get_project_info_success(self, projects_service, mock_repository):
        """Test successful project info retrieval."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        project_info = {
            "project": {"id": str(project_id), "name": "Test Project"},
            "members": [{"user_id": str(user_id), "role": "owner"}],
            "documents": []
        }
        
        mock_repository.get_project_info.return_value = project_info
        
        # Act
        result = projects_service.get_project_info(project_id, user_id)
        
        # Assert
        mock_repository.get_project_info.assert_called_once_with(project_id, user_id)
        assert result == project_info

    @pytest.mark.asyncio
    async def test_upload_project_documents_success(self, projects_service, mock_repository, mock_upload_files):
        """Test successful multiple document upload."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        documents = [
            Document(id=uuid4(), filename="test0.pdf", project_id=project_id,content_type= "pdf", size_bytes=20, storage_path="/path0"),
            Document(id=uuid4(), filename="test1.pdf", project_id=project_id, content_type= "pdf", size_bytes=20, storage_path="/path1")
        ]
        
        mock_repository.upload_project_documents = AsyncMock(return_value=documents)
        
        # Act
        result = await projects_service.upload_project_documents(
            project_id, user_id, mock_upload_files
        )
        
        # Assert
        mock_repository.upload_project_documents.assert_called_once_with(
            project_id, user_id, mock_upload_files
        )
        assert result == documents
        assert len(result) == 2

    def test_get_project_documents_success(self, projects_service, mock_repository):
        """Test successful project documents retrieval."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        documents = [
            {"id": str(uuid4()), "filename": "doc1.pdf"},
            {"id": str(uuid4()), "filename": "doc2.pdf"}
        ]
        
        mock_repository.get_project_documents.return_value = documents
        
        # Act
        result = projects_service.get_project_documents(project_id, user_id)
        
        # Assert
        mock_repository.get_project_documents.assert_called_once_with(project_id, user_id)
        assert result == documents

    def test_projects_service_initialization(self, mock_repository):
        """Test ProjectsService initialization with repository."""
        # Act
        service = ProjectsService(mock_repository)
        
        # Assert
        assert service.repository == mock_repository

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime
from fastapi import UploadFile
from io import BytesIO
from typing import BinaryIO
from app.domain.exceptions import (
    DocumentNotFoundError, InsufficientPermissionsError, UserNotFoundError, 
    PermissionDeniedError, ProjectNotFoundError, UserAlreadyMemberError
)
from app.domain.models import User, Project, Document, ProjectMembership, ProjectRole
from app.adapters.repositories.sqlalchemy.head_repository import SqlAlchemyRepository
from unittest.mock import AsyncMock, Mock, patch

class TestSqlAlchemyRepository:
    
    @pytest.fixture
    def mock_session(self):
        return Mock()
    
    @pytest.fixture
    def repository(self, mock_session):
        return SqlAlchemyRepository(mock_session)
    
    @pytest.fixture
    def sample_user_id(self):
        return uuid4()
    
    @pytest.fixture
    def sample_project_id(self):
        return uuid4()
    
    @pytest.fixture
    def sample_document_id(self):
        return uuid4()
    
    @pytest.fixture
    def sample_user(self, sample_user_id):
        return User(
            id=sample_user_id,
            name="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
    
    @pytest.fixture
    def sample_project(self, sample_project_id, sample_user_id):
        return Project(
            id=sample_project_id,
            name="Test Project",
            description="Test Description",
            owner_id=sample_user_id
        )
    
    @pytest.fixture
    def sample_document(self, sample_document_id, sample_project_id):
        return Document(
            id=sample_document_id,
            project_id=sample_project_id,
            filename="test.txt",
            content_type="text/plain",
            size_bytes=100,
            storage_path="/path/to/file",
            metadata={"description": "test file"}
        )
    
    @pytest.fixture
    def sample_membership(self, sample_project_id, sample_user_id):
        return ProjectMembership(
            project_id=sample_project_id,
            user_id=sample_user_id,
            role=ProjectRole.owner
        )
    
    @pytest.fixture
    def mock_upload_file(self):
        file_content = BytesIO(b"test content")
        return UploadFile(
            file=file_content,
            filename="test.txt",
            headers={"content-type": "text/plain"}
        )
    
    # @pytest.fixture
    # def sample_project_orm(self, sample_project_id, sample_user_id):
    #     """Create a sample ProjectORM instance."""
    #     project_orm = Mock(spec=ProjectORM)
    #     project_orm.id = sample_project_id
    #     project_orm.owner_id = sample_user_id
    #     project_orm.name = "Test Project"
    #     project_orm.description = "Test Description"
    #     project_orm.created_at = datetime.now()
    #     project_orm.updated_at = datetime.now()
    #     return project_orm

    # @pytest.fixture
    # def sample_user_orm(self, sample_user_id):
    #     """Create a sample UserORM instance."""
    #     user_orm = Mock(spec=UserORM)
    #     user_orm.id = sample_user_id
    #     user_orm.email = "test@example.com"
    #     user_orm.username = "testuser"
    #     user_orm.hashed_password = "hashed_password"
    #     user_orm.is_active = True
    #     user_orm.created_at = datetime.now()
    #     user_orm.updated_at = datetime.now()
    #     return user_orm
    # User Management Tests
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    def test_create_user_success(self, mock_users_repo_class, repository, mock_session):
        # Arrange
        mock_users_repo = Mock()
        mock_users_repo_class.return_value = mock_users_repo
        
        login = "testuser"
        password_hashed = "hashed_password"
        email = "test@example.com"
        
        expected_user = User(name=login, email=email, password_hash=password_hashed)
        mock_users_repo.add.return_value = expected_user
        
        # Act
        result = repository.create_user(login, password_hashed, email)
        
        # Assert
        mock_users_repo_class.assert_called_once_with(mock_session)
        mock_users_repo.add.assert_called_once()
        assert result.name == login
        assert result.email == email
        assert result.password_hash == password_hashed

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    def test_get_user_success(self, mock_users_repo_class, repository, mock_session, sample_user):
        # Arrange
        mock_users_repo = Mock()
        mock_users_repo_class.return_value = mock_users_repo
        mock_users_repo.get_by_name.return_value = sample_user
        
        # Act
        result = repository.get_user("testuser")
        
        # Assert
        mock_users_repo_class.assert_called_once_with(mock_session)
        mock_users_repo.get_by_name.assert_called_once_with("testuser")
        assert result == sample_user

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    def test_get_user_not_found(self, mock_users_repo_class, repository, mock_session):
        # Arrange
        mock_users_repo = Mock()
        mock_users_repo_class.return_value = mock_users_repo
        mock_users_repo.get_by_name.return_value = None
        
        # Act
        result = repository.get_user("nonexistent")
        
        # Assert
        assert result is None

    # Document Management Tests
    @patch('app.adapters.repositories.sqlalchemy.head_repository.LocalFileStorageAdapter')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyDocumentsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @pytest.mark.asyncio
    async def test_upload_document_success(self, mock_memberships_repo_class, mock_docs_repo_class, 
                                         mock_storage_class, repository, mock_session, 
                                         sample_project_id, sample_user_id, sample_membership, 
                                         mock_upload_file):
        # Arrange
        mock_memberships_repo = Mock()
        mock_docs_repo = Mock()
        mock_storage = AsyncMock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_docs_repo_class.return_value = mock_docs_repo
        mock_storage_class.return_value = mock_storage
        
        mock_memberships_repo.get.return_value = sample_membership
        
        file_metadata = Mock()
        file_metadata.filename = "test.txt"
        file_metadata.content_type = "text/plain"
        file_metadata.size_bytes = 100
        file_metadata.storage_path = "/path/to/file"
        file_metadata.metadata = {"description": "test"}
        
        mock_storage.save_file.return_value = file_metadata
        
        expected_document = Document(
            project_id=sample_project_id,
            filename="test.txt",
            content_type="text/plain",
            size_bytes=100,
            storage_path="/path/to/file",
            metadata={"description": "test"}
        )
        mock_docs_repo.add.return_value = expected_document
        
        # Act
        result = await repository.upload_document(
            sample_project_id, sample_user_id, mock_upload_file, "test.txt", "test description"
        )
        
        # Assert
        mock_memberships_repo.get.assert_called_once_with(sample_project_id, sample_user_id)
        mock_storage.save_file.assert_called_once()
        mock_docs_repo.add.assert_called_once()
        assert result == expected_document

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @pytest.mark.asyncio
    async def test_upload_document_insufficient_permissions(self, mock_memberships_repo_class, 
                                                          repository, mock_session, 
                                                          sample_project_id, sample_user_id, 
                                                          mock_upload_file):
        # Arrange
        mock_memberships_repo = Mock()
        mock_memberships_repo_class.return_value = mock_memberships_repo
        
        viewer_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=sample_user_id,
            role=ProjectRole.viewer
        )
        mock_memberships_repo.get.return_value = viewer_membership
        
        # Act & Assert
        with pytest.raises(InsufficientPermissionsError, match="Only editors and owners can upload documents"):
            await repository.upload_document(sample_project_id, sample_user_id, mock_upload_file)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.LocalFileStorageAdapter')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyDocumentsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @pytest.mark.asyncio
    async def test_download_document_success(self, mock_memberships_repo_class, mock_docs_repo_class,
                                           mock_storage_class, repository, mock_session,
                                           sample_document_id, sample_user_id, sample_document,
                                           sample_membership):
        # Arrange
        mock_memberships_repo = Mock()
        mock_docs_repo = Mock()
        mock_storage = AsyncMock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_docs_repo_class.return_value = mock_docs_repo
        mock_storage_class.return_value = mock_storage
        
        mock_docs_repo.get.return_value = sample_document
        mock_memberships_repo.get.return_value = sample_membership
        
        binary_file = BytesIO(b"test content")
        mock_storage.get_file.return_value = binary_file
        
        # Act
        file, document = await repository.download_document(sample_document_id, sample_user_id)
        
        # Assert
        mock_docs_repo.get.assert_called_once_with(sample_document_id)
        mock_memberships_repo.get.assert_called_once_with(sample_document.project_id, sample_user_id)
        mock_storage.get_file.assert_called_once_with(sample_document.storage_path)
        assert isinstance(file, BytesIO)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyDocumentsRepository')
    @pytest.mark.asyncio
    async def test_download_document_not_found(self, mock_docs_repo_class, repository, 
                                             mock_session, sample_document_id, sample_user_id):
        # Arrange
        mock_docs_repo = Mock()
        mock_docs_repo_class.return_value = mock_docs_repo
        mock_docs_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(DocumentNotFoundError, match=f"Document with id {sample_document_id} not found"):
            await repository.download_document(sample_document_id, sample_user_id)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyDocumentsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_update_document_success(self, mock_memberships_repo_class, mock_docs_repo_class,
                                   repository, mock_session, sample_document_id, sample_user_id,
                                   sample_document, sample_membership):
        # Arrange
        mock_memberships_repo = Mock()
        mock_docs_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_docs_repo_class.return_value = mock_docs_repo
        
        mock_docs_repo.get.return_value = sample_document
        mock_memberships_repo.get.return_value = sample_membership
        
        updated_document = Document(
            id=sample_document_id,
            project_id=sample_document.project_id,
            filename="updated.txt",
            content_type=sample_document.content_type,
            size_bytes=sample_document.size_bytes,
            storage_path=sample_document.storage_path,
            metadata={"updated": "metadata"}
        )
        mock_docs_repo.update.return_value = updated_document
        
        # Act
        result = repository.update_document(
            sample_document_id, sample_user_id, 
            filename="updated.txt", metadata={"updated": "metadata"}
        )
        
        # Assert
        mock_docs_repo.get.assert_called_once_with(sample_document_id)
        mock_memberships_repo.get.assert_called_once_with(sample_document.project_id, sample_user_id)
        mock_docs_repo.update.assert_called_once()
        assert result == updated_document

    @patch('app.adapters.repositories.sqlalchemy.head_repository.LocalFileStorageAdapter')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyDocumentsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @pytest.mark.asyncio
    async def test_delete_document_success(self, mock_memberships_repo_class, mock_docs_repo_class,
                                         mock_storage_class, repository, mock_session,
                                         sample_document_id, sample_user_id, sample_document,
                                         sample_membership):
        # Arrange
        mock_memberships_repo = Mock()
        mock_docs_repo = Mock()
        mock_storage = AsyncMock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_docs_repo_class.return_value = mock_docs_repo
        mock_storage_class.return_value = mock_storage
        
        mock_docs_repo.get.return_value = sample_document
        mock_memberships_repo.get.return_value = sample_membership
        
        # Act
        await repository.delete_document(sample_document_id, sample_user_id)
        
        # Assert
        mock_docs_repo.get.assert_called_once_with(sample_document_id)
        mock_memberships_repo.get.assert_called_once_with(sample_document.project_id, sample_user_id)
        mock_storage.delete_file.assert_called_once_with(sample_document.storage_path)
        mock_docs_repo.delete.assert_called_once_with(sample_document_id)

    # Project Management Tests
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_create_project_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                                repository, sample_user_id, sample_project):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo

        
        mock_projects_repo.add.return_value = sample_project
        
        # Act
        result = repository.create_project("Test Project", "Test Description", sample_user_id)
        
        # Assert
        mock_projects_repo.add.assert_called_once()
        mock_memberships_repo.add.assert_called_once()
        assert result == sample_project

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_get_project_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                               repository, mock_session, sample_project_id, sample_user_id,
                               sample_project, sample_membership):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        mock_projects_repo.get.return_value = sample_project
        mock_memberships_repo.get.return_value = sample_membership
        
        # Act
        result = repository.get_project(sample_project_id, sample_user_id)
        
        # Assert
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        mock_memberships_repo.get.assert_called_once_with(sample_project_id, sample_user_id)
        assert result == sample_project

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    def test_get_project_not_found(self, mock_projects_repo_class, repository, 
                                 mock_session, sample_project_id, sample_user_id):
        # Arrange
        mock_projects_repo = Mock()
        mock_projects_repo_class.return_value = mock_projects_repo
        mock_projects_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(ProjectNotFoundError, match=f"Project with id {sample_project_id} not found"):
            repository.get_project(sample_project_id, sample_user_id)

    # Project Membership Tests
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_invite_user_to_project_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                                          mock_users_repo_class, repository, mock_session,
                                          sample_project_id, sample_user_id):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        mock_users_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        mock_users_repo_class.return_value = mock_users_repo
        
        inviter_id = uuid4()
        invited_user_id = uuid4()
        
        sample_project = Project(id=sample_project_id, name="Test", description="Test", owner_id=inviter_id)
        inviter_membership = ProjectMembership(project_id=sample_project_id, user_id=inviter_id, role=ProjectRole.owner)
        invited_user = User(id=invited_user_id, name="invited", email="invited@test.com", password_hash="hash")
        
        mock_projects_repo.get.return_value = sample_project
        mock_memberships_repo.get.side_effect = [inviter_membership, None]  # inviter exists, invited doesn't
        mock_users_repo.get.return_value = invited_user
        
        new_membership = ProjectMembership(project_id=sample_project_id, user_id=invited_user_id, role=ProjectRole.editor)
        mock_memberships_repo.add.return_value = new_membership
        
        # Act
        result = repository.invite_user_to_project(sample_project_id, inviter_id, invited_user_id, ProjectRole.editor)
        
        # Assert
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        assert mock_memberships_repo.get.call_count == 2
        mock_users_repo.get.assert_called_once_with(invited_user_id)
        mock_memberships_repo.add.assert_called_once()
        assert result == new_membership

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_invite_user_already_member(self, mock_memberships_repo_class, mock_projects_repo_class,
                                      mock_users_repo_class, repository, mock_session,
                                      sample_project_id):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        mock_users_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        mock_users_repo_class.return_value = mock_users_repo
        
        inviter_id = uuid4()
        invited_user_id = uuid4()
        
        sample_project = Project(id=sample_project_id, name="Test", description="Test", owner_id=inviter_id)
        inviter_membership = ProjectMembership(project_id=sample_project_id, user_id=inviter_id, role=ProjectRole.owner)
        existing_membership = ProjectMembership(project_id=sample_project_id, user_id=invited_user_id, role=ProjectRole.viewer)
        invited_user = User(id=invited_user_id, name="invited", email="invited@test.com", password_hash="hash")
        
        mock_projects_repo.get.return_value = sample_project
        mock_memberships_repo.get.side_effect = [inviter_membership, existing_membership]
        mock_users_repo.get.return_value = invited_user
        
        # Act & Assert
        with pytest.raises(UserAlreadyMemberError, match="User is already a member of this project"):
            repository.invite_user_to_project(sample_project_id, inviter_id, invited_user_id, ProjectRole.editor)

    # Additional edge cases and error scenarios
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @pytest.mark.asyncio
    async def test_upload_document_no_membership(self, mock_memberships_repo_class, repository, 
                                               mock_session, sample_project_id, sample_user_id, 
                                               mock_upload_file):
        # Arrange
        mock_memberships_repo = Mock()
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_memberships_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(InsufficientPermissionsError, match="Only editors and owners can upload documents"):
            await repository.upload_document(sample_project_id, sample_user_id, mock_upload_file)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    def test_get_user_projects_success(self, mock_projects_repo_class, mock_memberships_repo_class, 
                                     mock_users_repo_class, repository, mock_session, sample_user_id, sample_user):
        # Arrange
        mock_memberships_repo = Mock()
        mock_users_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_users_repo_class.return_value = mock_users_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        mock_users_repo.get.return_value = sample_user
        
        project1_id = uuid4()
        project2_id = uuid4()
        
        memberships = [
            ProjectMembership(project_id=project1_id, user_id=sample_user_id, role=ProjectRole.owner),
            ProjectMembership(project_id=project2_id, user_id=sample_user_id, role=ProjectRole.editor)
        ]
        mock_memberships_repo.list_by_user.return_value = memberships
        
        projects = [
            Project(id=project1_id, name="Project 1", description="Desc 1", owner_id=sample_user_id),
            Project(id=project2_id, name="Project 2", description="Desc 2", owner_id=uuid4())
        ]
        
        mock_projects_repo.get.side_effect = projects
        
        # Act
        result = repository.get_user_projects(sample_user_id)
        
        # Assert
        mock_users_repo.get.assert_called_once_with(sample_user_id)
        mock_memberships_repo.list_by_user.assert_called_once_with(sample_user_id)
        assert len(result) == 2
        assert result == projects

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_update_project_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                                  repository, mock_session, sample_project_id, sample_user_id,
                                  sample_project, sample_membership):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        mock_projects_repo.get.return_value = sample_project
        mock_memberships_repo.get.return_value = sample_membership
        
        updated_project = Project(
            id=sample_project_id,
            name="Updated Project",
            description="Updated Description",
            owner_id=sample_user_id
        )
        mock_projects_repo.update.return_value = updated_project
        
        # Act
        result = repository.update_project(
            sample_project_id, sample_user_id, 
            name="Updated Project", description="Updated Description"
        )
        
        # Assert
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        mock_memberships_repo.get.assert_called_once_with(sample_project_id, sample_user_id)
        mock_projects_repo.update.assert_called_once()
        assert result == updated_project

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_update_project_insufficient_permissions(self, mock_memberships_repo_class, mock_projects_repo_class,
                                                   repository, mock_session, sample_project_id, sample_user_id,
                                                   sample_project):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        mock_projects_repo.get.return_value = sample_project
        
        viewer_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=sample_user_id,
            role=ProjectRole.viewer
        )
        mock_memberships_repo.get.return_value = viewer_membership
        
        # Act & Assert
        with pytest.raises(InsufficientPermissionsError, match="You don't have permission to edit this project"):
            repository.update_project(sample_project_id, sample_user_id, name="Updated")

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_delete_project_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                                  repository, mock_session, sample_project_id, sample_user_id,
                                  sample_project, sample_membership):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        mock_projects_repo.get.return_value = sample_project
        mock_memberships_repo.get.return_value = sample_membership
        mock_projects_repo.delete.return_value = True
        
        # Act
        result = repository.delete_project(sample_project_id, sample_user_id)
        
        # Assert
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        mock_memberships_repo.get.assert_called_once_with(sample_project_id, sample_user_id)
        mock_memberships_repo.delete_by_project.assert_called_once_with(sample_project_id)
        mock_projects_repo.delete.assert_called_once_with(sample_project_id)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_delete_project_not_owner(self, mock_memberships_repo_class, mock_projects_repo_class,
                                    repository, mock_session, sample_project_id, sample_user_id,
                                    sample_project):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        mock_projects_repo.get.return_value = sample_project
        
        editor_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=sample_user_id,
            role=ProjectRole.editor
        )
        mock_memberships_repo.get.return_value = editor_membership
        
        # Act & Assert
        with pytest.raises(InsufficientPermissionsError, match="Only project owner can delete the project"):
            repository.delete_project(sample_project_id, sample_user_id)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    def test_update_user_role_success(self, mock_projects_repo_class, mock_memberships_repo_class, 
                                    mock_users_repo_class, repository, mock_session, 
                                    sample_project_id, sample_user_id):
        """Test successful user role update."""
        # Arrange
        mock_projects_repo = Mock()
        mock_memberships_repo = Mock()
        mock_users_repo = Mock()
        
        mock_projects_repo_class.return_value = mock_projects_repo
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_users_repo_class.return_value = mock_users_repo
        
        updater_id = uuid4()
        target_user_id = uuid4()
        
        # Mock project exists - return a proper Project domain object
        sample_project = Project(
            id=sample_project_id,
            owner_id=sample_user_id,
            name="Test Project",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_projects_repo.get.return_value = sample_project
        
        # Mock memberships
        updater_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=updater_id,
            role=ProjectRole.owner
        )
        
        target_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=target_user_id,
            role=ProjectRole.viewer
        )
        
        # Mock membership repository calls
        mock_memberships_repo.get.side_effect = [updater_membership, target_membership]
        
        updated_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=target_user_id,
            role=ProjectRole.editor
        )
        mock_memberships_repo.update.return_value = updated_membership
        
        # Act
        result = repository.update_user_role(sample_project_id, updater_id, target_user_id, ProjectRole.editor)
        
        # Assert
        assert result == updated_membership
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        assert mock_memberships_repo.get.call_count == 2
        mock_memberships_repo.update.assert_called_once()

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    def test_update_user_role_cannot_change_owner(self, mock_projects_repo_class, mock_memberships_repo_class,
                                                 mock_users_repo_class, repository, sample_project_id, sample_user_id):
        """Test that owner role cannot be changed."""
        # Arrange
        mock_projects_repo = Mock()
        mock_memberships_repo = Mock()
        mock_users_repo = Mock()
        
        mock_projects_repo_class.return_value = mock_projects_repo
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_users_repo_class.return_value = mock_users_repo
        
        updater_id = uuid4()
        target_user_id = uuid4()
        
        # Mock project exists
        sample_project = Project(
            id=sample_project_id,
            owner_id=sample_user_id,
            name="Test Project",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_projects_repo.get.return_value = sample_project
        
        # Mock updater has owner permissions
        updater_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=updater_id,
            role=ProjectRole.owner
        )
        
        # Mock target user is also an owner
        target_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=target_user_id,
            role=ProjectRole.owner
        )
        
        mock_memberships_repo.get.side_effect = [updater_membership, target_membership]
        
        # Act & Assert
        with pytest.raises(InsufficientPermissionsError, match="Cannot change owner role"):
            repository.update_user_role(sample_project_id, updater_id, target_user_id, ProjectRole.editor)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_remove_user_from_project_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                                            repository, mock_session, sample_project_id, sample_project):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        remover_id = uuid4()
        target_user_id = uuid4()
        
        mock_projects_repo.get.return_value = sample_project
        
        remover_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=remover_id,
            role=ProjectRole.owner
        )
        
        target_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=target_user_id,
            role=ProjectRole.editor
        )
        
        mock_memberships_repo.get.side_effect = [remover_membership, target_membership]
        mock_memberships_repo.delete.return_value = True
        
        # Act
        result = repository.remove_user_from_project(sample_project_id, remover_id, target_user_id)
        
        # Assert
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        assert mock_memberships_repo.get.call_count == 2
        mock_memberships_repo.delete.assert_called_once_with(sample_project_id, target_user_id)
        assert result is True

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_remove_user_cannot_remove_owner(self, mock_memberships_repo_class, mock_projects_repo_class,
                                           repository, mock_session, sample_project_id, sample_project):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        
        remover_id = uuid4()
        target_user_id = uuid4()
        
        mock_projects_repo.get.return_value = sample_project
        
        remover_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=remover_id,
            role=ProjectRole.owner
        )
        
        target_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=target_user_id,
            role=ProjectRole.owner
        )
        
        mock_memberships_repo.get.side_effect = [remover_membership, target_membership]
        
        # Act & Assert
        with pytest.raises(InsufficientPermissionsError, match="Cannot remove project owner"):
            repository.remove_user_from_project(sample_project_id, remover_id, target_user_id)

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyUsersRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyDocumentsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_get_project_info_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                                    mock_docs_repo_class, mock_users_repo_class,
                                    repository, mock_session, sample_project_id, sample_user_id,
                                    sample_project, sample_membership, sample_document):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        mock_docs_repo = Mock()
        mock_users_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        mock_docs_repo_class.return_value = mock_docs_repo
        mock_users_repo_class.return_value = mock_users_repo
        
        mock_projects_repo.get.return_value = sample_project
        mock_memberships_repo.get.return_value = sample_membership
        
        # Mock project members
        member_user = User(id=uuid4(), name="member", email="member@test.com", password_hash="hash")
        memberships = [sample_membership]
        mock_memberships_repo.list_by_project.return_value = memberships
        mock_users_repo.get.return_value = member_user
        
        # Mock documents
        documents = [sample_document]
        mock_docs_repo.list_by_project.return_value = documents
        
        # Act
        result = repository.get_project_info(sample_project_id, sample_user_id)
        
        # Assert
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        mock_memberships_repo.get.assert_called_once_with(sample_project_id, sample_user_id)
        mock_memberships_repo.list_by_project.assert_called_once_with(sample_project_id)
        mock_docs_repo.list_by_project.assert_called_once_with(sample_project_id)
        
        assert result["project"] == sample_project
        assert len(result["members"]) == 1
        assert result["members"][0] == [sample_membership.role, member_user]
        assert result["documents"] == documents

    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyDocumentsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectsRepository')
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    def test_get_project_documents_success(self, mock_memberships_repo_class, mock_projects_repo_class,
                                         mock_docs_repo_class, repository, mock_session,
                                         sample_project_id, sample_user_id, sample_project,
                                         sample_membership, sample_document):
        # Arrange
        mock_memberships_repo = Mock()
        mock_projects_repo = Mock()
        mock_docs_repo = Mock()
        
        mock_memberships_repo_class.return_value = mock_memberships_repo
        mock_projects_repo_class.return_value = mock_projects_repo
        mock_docs_repo_class.return_value = mock_docs_repo
        
        mock_projects_repo.get.return_value = sample_project
        mock_memberships_repo.get.return_value = sample_membership
        
        documents = [sample_document]
        mock_docs_repo.list_by_project.return_value = documents
        
        # Act
        result = repository.get_project_documents(sample_project_id, sample_user_id)
        
        # Assert
        mock_projects_repo.get.assert_called_once_with(sample_project_id)
        mock_memberships_repo.get.assert_called_once_with(sample_project_id, sample_user_id)
        mock_docs_repo.list_by_project.assert_called_once_with(sample_project_id)
        assert result == documents
            
    @pytest.mark.asyncio
    @patch('app.adapters.repositories.sqlalchemy.head_repository.SqlAlchemyProjectMembershipsRepository')
    async def test_upload_project_documents_insufficient_permissions(self, mock_memberships_repo_class,
                                                             repository, mock_session,
                                                             sample_project_id, sample_user_id,
                                                             mock_upload_file):
        # Arrange
        mock_memberships_repo = Mock()
        mock_memberships_repo_class.return_value = mock_memberships_repo
        
        viewer_membership = ProjectMembership(
            project_id=sample_project_id,
            user_id=sample_user_id,
            role=ProjectRole.viewer
        )
        mock_memberships_repo.get.return_value = viewer_membership
        
        # Act & Assert
        with pytest.raises(InsufficientPermissionsError, match="Only editors and owners can upload documents"):
            await repository.upload_project_documents(sample_project_id, sample_user_id, [mock_upload_file])

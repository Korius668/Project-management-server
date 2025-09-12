"""Integration tests for service layer."""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock
from io import BytesIO

from app.usecases.auth import AuthService
from app.usecases.projects import ProjectsService
from app.usecases.documents import DocumentsService
from app.domain.models import User, Project, Document, ProjectRole
from app.domain.exceptions import (
    AuthenticationError,
    UserNotFoundError,
    ProjectNotFoundError,
    InsufficientPermissionsError,
)


class TestAuthService:
    """Test authentication service integration."""

    def test_create_user_success(self, test_repository):
        """Test successful user creation."""
        auth_service = AuthService(test_repository)

        result = auth_service.create_user("testuser", "password123", "test@example.com")

        assert result is not None
        assert result.name == "testuser"
        assert result.email == "test@example.com"
        # Password should be hashed
        assert result.password_hash != "password123"

    def test_login_success(self, test_repository):
        """Test successful login."""
        auth_service = AuthService(test_repository)

        # Create user first
        user = auth_service.create_user("testuser", "password123", "test@example.com")

        # Login with email
        token = auth_service.login("testuser", "password123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_login_invalid_credentials_raises_error(self, test_repository):
        """Test login with invalid credentials."""
        auth_service = AuthService(test_repository)

        # Create user first
        auth_service.create_user("testuser", "password123", "test@example.com")

        # Try login with wrong password
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.login("test@example.com", "wrongpassword")

    def test_login_nonexistent_user_raises_error(self, test_repository):
        """Test login with non-existent user."""
        auth_service = AuthService(test_repository)

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            auth_service.login("nonexistent@example.com", "password123")


class TestProjectsService:
    """Test projects service integration."""

    def test_create_project_success(self, test_repository):
        """Test successful project creation."""
        # Create user first
        auth_service = AuthService(test_repository)
        user = auth_service.create_user("owner", "password123", "owner@example.com")

        projects_service = ProjectsService(test_repository)

        result = projects_service.create_project(
            "Test Project", "A test project", user.id
        )

        assert result is not None
        assert result.name == "Test Project"
        assert result.description == "A test project"
        assert result.owner_id == user.id

    def test_get_project_success(self, test_repository):
        """Test getting project with access."""
        # Create user and project
        auth_service = AuthService(test_repository)
        user = auth_service.create_user("owner", "password123", "owner@example.com")

        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", user.id)

        result = projects_service.get_project(project.id, user.id)

        assert result is not None
        assert result.id == project.id
        assert result.name == "Test Project"

    def test_get_project_no_access_raises_error(self, test_repository):
        """Test getting project without access raises error."""
        # Create two users
        auth_service = AuthService(test_repository)
        owner = auth_service.create_user("owner", "password123", "owner@example.com")
        other_user = auth_service.create_user(
            "other", "password123", "other@example.com"
        )

        # Create project as owner
        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", owner.id)

        # Try to access as other user (should fail)
        with pytest.raises(Exception):  # Should raise PermissionDeniedError
            projects_service.get_project(project.id, other_user.id)

    def test_update_project_success(self, test_repository):
        """Test updating project."""
        # Create user and project
        auth_service = AuthService(test_repository)
        user = auth_service.create_user("owner", "password123", "owner@example.com")

        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Original Name", "Original", user.id)

        result = projects_service.update_project(
            project.id, user.id, name="Updated Name", description="Updated description"
        )

        assert result is not None
        assert result.name == "Updated Name"
        assert result.description == "Updated description"

    def test_invite_user_to_project_success(self, test_repository):
        """Test inviting user to project."""
        # Create users
        auth_service = AuthService(test_repository)
        owner = auth_service.create_user("owner", "password123", "owner@example.com")
        member = auth_service.create_user("member", "password123", "member@example.com")

        # Create project
        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", owner.id)

        # Invite member
        result = projects_service.invite_user_to_project(
            project.id, owner.id, member.id, ProjectRole.editor
        )

        assert result is not None
        assert result.project_id == project.id
        assert result.user_id == member.id
        assert result.role == ProjectRole.editor

    def test_update_user_role_success(self, test_repository):
        """Test updating user role in project."""
        # Create users
        repo = test_repository
        auth_service = AuthService(repo)
        owner = auth_service.create_user("owner", "password123", "owner@example.com")
        member = auth_service.create_user("member", "password123", "member@example.com")

        # Create project and invite member
        projects_service = ProjectsService(repo)
        project = projects_service.create_project("Test Project", "Test", owner.id)
        projects_service.invite_user_to_project(
            project.id, owner.id, member.id, ProjectRole.viewer
        )

        result = projects_service.update_user_role(
            project.id, owner.id, member.id, ProjectRole.editor
        )

        assert result is not None
        assert result.role == ProjectRole.editor

    def test_remove_user_from_project_success(self, test_repository):
        """Test removing user from project."""
        # Create users
        auth_service = AuthService(test_repository)
        owner = auth_service.create_user("owner", "password123", "owner@example.com")
        member = auth_service.create_user("member", "password123", "member@example.com")

        # Create project and invite member
        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", owner.id)
        projects_service.invite_user_to_project(
            project.id, owner.id, member.id, ProjectRole.editor
        )

        # Remove member
        result = projects_service.remove_user_from_project(
            project.id, owner.id, member.id
        )

        assert result is True


class TestDocumentsService:
    """Test documents service integration."""

    @pytest.fixture
    def mock_upload_file(self):
        """Create mock upload file."""
        mock_file = Mock()
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"
        mock_file.file = BytesIO(b"test content")
        return mock_file

    @pytest.mark.asyncio
    async def test_upload_document_success(self, test_repository, mock_upload_file):
        """Test successful document upload."""
        # Create user and project
        auth_service = AuthService(test_repository)
        user = auth_service.create_user("owner", "password123", "owner@example.com")

        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", user.id)

        # Mock the repository's upload_document method
        expected_document = Document(
            project_id=project.id,
            filename="test.txt",
            content_type="text/plain",
            size_bytes=12,
            storage_path="project-1/test.txt",
            metadata={"description": "Test file"},
        )
        test_repository.upload_document = AsyncMock(return_value=expected_document)

        documents_service = DocumentsService(test_repository)

        result = await documents_service.upload_document(
            project.id,
            user.id,
            mock_upload_file,
            name="test.txt",
            description="Test file",
        )

        assert result is not None
        assert result.filename == "test.txt"
        assert result.project_id == project.id

    @pytest.mark.asyncio
    async def test_download_document_success(self, test_repository):
        """Test successful document download."""
        # Create user and project
        auth_service = AuthService(test_repository)
        user = auth_service.create_user("owner", "password123", "owner@example.com")

        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", user.id)

        # Mock document and download
        document_id = uuid.uuid4()
        expected_file = BytesIO(b"test file content")
        test_repository.download_document = AsyncMock(return_value=expected_file)

        documents_service = DocumentsService(test_repository)

        result = await documents_service.download_document(document_id, user.id)

        assert result is not None
        assert isinstance(result, BytesIO)

    def test_update_document_success(self, test_repository):
        """Test updating document metadata."""
        # Create user and project
        auth_service = AuthService(test_repository)
        user = auth_service.create_user("owner", "password123", "owner@example.com")

        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", user.id)

        # Mock document update
        document_id = uuid.uuid4()
        expected_document = Document(
            id=document_id,
            project_id=project.id,
            filename="updated.txt",
            content_type="text/plain",
            size_bytes=12,
            storage_path="project-1/updated.txt",
            metadata_={"updated": True},
        )
        test_repository.update_document = Mock(return_value=expected_document)

        documents_service = DocumentsService(test_repository)

        result = documents_service.update_document(
            document_id, user.id, filename="updated.txt", metadata={"updated": True}
        )

        assert result is not None
        assert result.filename == "updated.txt"
        assert result.metadata_ == {"updated": True}

    @pytest.mark.asyncio
    async def test_delete_document_success(self, test_repository):
        """Test deleting document."""
        # Create user and project
        auth_service = AuthService(test_repository)
        user = auth_service.create_user("owner", "password123", "owner@example.com")

        projects_service = ProjectsService(test_repository)
        project = projects_service.create_project("Test Project", "Test", user.id)

        # Mock document deletion
        document_id = uuid.uuid4()
        test_repository.delete_document = AsyncMock(return_value=None)

        documents_service = DocumentsService(test_repository)

        # Should not raise any exception
        await documents_service.delete_document(document_id, user.id)

        # Verify the repository method was called
        test_repository.delete_document.assert_called_once_with(document_id, user.id)

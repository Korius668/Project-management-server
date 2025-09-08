from unittest.mock import Mock
import pytest
from uuid import uuid4
from io import BytesIO

from app.domain.models import Document, User, ProjectRole, Project, ProjectMembership
from app.ports.file_storage import FileMetadata


@pytest.fixture(scope="class")
def user1():
    """Sample user for testing"""
    return User(
        id=uuid4(),
        email="test@example.com",
        name="testuser",
        password_hash="$2b$12$hashed_password",
    )


@pytest.fixture(scope="class")
def project1(user1):
    """Sample project for testing"""
    return Project(
        id=uuid4(),
        owner_id=user1.id,
        name="Test Project",
        description="Test Description",
    )


@pytest.fixture(scope="class")
def membership1(user1, project1):
    """Sample project membership for testing"""
    return ProjectMembership(
        project_id=project1.id,
        user_id=user1.id,
        role=ProjectRole.owner,  # Fixed enum value from EDITOR to editor
    )


@pytest.fixture(scope="class")
def document1(project1):
    return Document(
        id=uuid4(),
        project_id=project1.id,
        filename="sample_document",
        content_type="sample_type",
        size_bytes=132156,
        storage_path="sajmasfl",
        metadata=None,
    )


@pytest.fixture(scope="class")
def filemetadata1(document1):
    return FileMetadata(
        filename=document1.filename,
        content_type=document1.content_type,
        size_bytes=document1.size_bytes,
        storage_path=document1.storage_path,
        metadata=document1.metadata,
    )


@pytest.fixture(scope="class")
def mock_upload_file1(filemetadata1):
    """Mock upload file 1 for testing"""
    mock_file = Mock()
    mock_file.filename = filemetadata1.filename
    mock_file.content_type = filemetadata1.content_type
    mock_file.size = filemetadata1.size_bytes
    mock_file.file = BytesIO(b"test file content")
    return mock_file


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
        password_hash="hashedpass",
    )


@pytest.fixture
def another_user():
    """Another sample user for testing"""
    return User(
        id=uuid4(),
        email="another@example.com",
        name="anotheruser",
        password_hash="$2b$12$hashed_password",
    )


@pytest.fixture
def editor_membership(another_user, sample_project):
    """Sample editor membership for testing"""
    return ProjectMembership(
        project_id=sample_project.id, user_id=another_user.id, role=ProjectRole.editor
    )

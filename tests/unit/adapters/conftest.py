import pytest
from uuid import uuid4
from unittest.mock import Mock
from app.domain.models import User, Project, Document, ProjectMembership, ProjectRole


@pytest.fixture
def sample_user():
    """Przykładowy użytkownik do testów"""
    return User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password_123",
    )


@pytest.fixture
def sample_project():
    """Przykładowy projekt do testów"""
    return Project(
        id=uuid4(),
        owner_id=uuid4(),
        name="Test Project",
        description="Test Description",
    )


@pytest.fixture
def sample_document():
    """Przykładowy dokument do testów"""
    return Document(
        id=uuid4(),
        project_id=uuid4(),
        filename="test.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        storage_path="/storage/test.pdf",
        metadata={"uploader_id": str(uuid4()), "version": 1},
    )


@pytest.fixture
def sample_membership():
    """Przykładowe członkostwo do testów"""
    return ProjectMembership(
        project_id=uuid4(), user_id=uuid4(), role=ProjectRole.editor
    )


@pytest.fixture
def mock_session():
    return Mock()

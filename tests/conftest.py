import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from uuid import uuid4
from sqlalchemy.orm import Session

from app.domain.models import User, Project, ProjectMembership, ProjectRole
from app.ports.repositories import (
    UsersRepository,
    ProjectsRepository,
    ProjectMembershipsRepository,
)


from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def new_user():
    """Creates a test user and returns its credentials"""
    payload = {"login": "user_1", "password": "VerySafePass123"}
    client.post("/auth/sign_up", json=payload)
    return payload


@pytest.fixture
def access_token(new_user):
    """Logs in the new_user and returns their access token"""
    response = client.post("/auth/login", json=new_user)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return token


@pytest.fixture
def new_project(client, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"name": "My Test Project", "description": "Test description"}
    response = client.put("/projects/1/info", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_memberships_repository():
    """Mock project memberships repository"""
    return Mock(spec=ProjectMembershipsRepository)


@pytest.fixture
def mock_users_repository():
    """Mock users repository"""
    return Mock(spec=UsersRepository)


@pytest.fixture
def mock_projects_repository():
    """Mock projects repository"""
    return Mock(spec=ProjectsRepository)


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return User(
        id=uuid4(),
        email="test@example.com",
        name="testuser",
        password_hash="$2b$12$hashed_password",
    )


@pytest.fixture
def sample_project():
    """Sample project for testing"""
    return Project(
        id=uuid4(),
        owner_id=uuid4(),
        name="Test Project",
        description="Test Description",
    )


@pytest.fixture
def sample_membership():
    """Sample project membership for testing"""
    return ProjectMembership(
        project_id=uuid4(), user_id=uuid4(), role=ProjectRole.editor
    )

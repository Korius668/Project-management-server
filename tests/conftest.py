import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import shutil
from pathlib import Path
import uuid

from app.main import get_application
from app.adapters.repositories.sqlalchemy.models import Base
from app.infrastructure.db.db import get_session
from app.adapters.repositories.sqlalchemy.head_repository import SqlAlchemyRepository
from app.config import Settings, Secrets


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_secrets():
    """Test configuration secrets."""
    return Secrets(
        secret_key="test-secret-key-for-jwt-tokens-in-tests",
        algorithm="HS256",
        access_token_expire_minutes=30,
        file_storage_path="./test_files",
        max_file_size_mb=10,
        database_url_prod=None
    )


@pytest.fixture(scope="session")
def test_settings(test_secrets):
    """Test application settings."""
    return Settings(app_env="test", secrets=test_secrets)


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine with in-memory SQLite."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_repository(test_session):
    """Create test repository instance."""
    return SqlAlchemyRepository(test_session)


@pytest.fixture(scope="function")
def temp_file_storage():
    """Create temporary directory for file storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def test_app(test_session, test_settings, temp_file_storage):
    """Create test FastAPI application."""
    app = get_application()

    # Override dependencies
    def override_get_session():
        return test_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    # Override file storage path in settings directly
    test_settings.secrets.file_storage_path = str(temp_file_storage)
    
    # Override the global settings
    from app.config import settings
    original_settings = settings
    settings = test_settings
    
    yield app
    
    # Clean up
    app.dependency_overrides.clear()
    settings = original_settings


@pytest.fixture(scope="function")
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture(scope="function")
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "password": "testpassword123"
    }


@pytest.fixture(scope="function")
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": f"Test Project {uuid.uuid4().hex[:8]}",
        "description": "A test project for integration testing"
    }


@pytest.fixture(scope="function")
def authenticated_user(test_client, sample_user_data):
    """Create and authenticate a test user."""
    # Create user
    response = test_client.post(
        "/auth/create_user",
        params=sample_user_data
    )
    assert response.status_code == 201
    user_data = response.json()
    
    # Login to get token
    login_response = test_client.post(
        "/auth/login",
        params={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    
    result = {
        "user": user_data,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
    }
    return result


@pytest.fixture(scope="function")
def test_project(test_client, authenticated_user, sample_project_data):
    """Create a test project."""
    response = test_client.post(
        "/projects/",
        json=sample_project_data,
        headers=authenticated_user["headers"]
    )
    assert response.status_code == 201
    result = response.json()
    return result


@pytest.fixture(scope="function")
def sample_file_content():
    """Sample file content for document testing."""
    return b"This is test file content for document upload testing."


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_database(test_session):
    """Clean up database after each test."""
    yield
    # Rollback any uncommitted changes
    test_session.rollback()

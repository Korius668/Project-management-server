import io
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock
from types import SimpleNamespace

from app.api.projects import projects, get_projects_service
from fastapi import FastAPI

# ---- PATCH DEPENDENCIES ----

def fake_token_to_user():
    return uuid4()

@pytest.fixture
def client():
    app = FastAPI()
    service = MagicMock()

    app.dependency_overrides[get_projects_service] = lambda: service

    import app.api.projects as routes
    app.dependency_overrides[routes.token_to_user] = fake_token_to_user

    app.include_router(projects)
    return TestClient(app)

@pytest.fixture
def mock_service(client):
    return client.app.dependency_overrides[get_projects_service]()

# ---- HELPERS ----

class FakeMembership:
    def __init__(self, user_id, role: str):
        self.user_id = user_id
        self.role = SimpleNamespace(value=role)

class FakeDocument:
    def __init__(self, id, filename):
        self.id = id
        self.filename = filename
        self.content_type = "application/pdf"
        self.size_bytes = 123
        self.storage_path = "/tmp/file.pdf"

# ---- TESTY ----

def test_create_project(client, mock_service):
    project = SimpleNamespace(id=uuid4(), name="Test Project", description="Opis")
    mock_service.create_project.return_value = project

    response = client.post("/projects/", json={"name": "Test Project", "description": "Opis"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    mock_service.create_project.assert_called_once()

def test_get_project(client, mock_service):
    project = SimpleNamespace(id=uuid4(), name="Proj", description="Desc")
    mock_service.get_project.return_value = project

    response = client.get(f"/projects/{project.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(project.id)
    mock_service.get_project.assert_called_once()

def test_update_project_info(client, mock_service):
    project = SimpleNamespace(id=uuid4(), name="Updated", description="Nowy opis")
    mock_service.update_project.return_value = project

    response = client.put(f"/projects/{project.id}/info", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    mock_service.update_project.assert_called_once()

def test_delete_project(client, mock_service):
    project_id = uuid4()
    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 200
    mock_service.delete_project.assert_called_once()

def test_list_project_documents(client, mock_service):
    project_id = uuid4()
    doc = FakeDocument(uuid4(), "plik.pdf")
    mock_service.get_project_documents.return_value = [doc]

    response = client.get(f"/projects/{project_id}/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["uploaded_documents"][0]["filename"] == "plik.pdf"
    mock_service.get_project_documents.assert_called_once()

def test_upload_documents(client, mock_service):
    project_id = uuid4()
    doc = FakeDocument(uuid4(), "plik.txt")

    # upload_project_documents musi być awaitowalne
    mock_service.upload_project_documents = AsyncMock(return_value=[doc])

    files = {"files": ("plik.txt", io.BytesIO(b"abc"), "text/plain")}
    response = client.post(f"/projects/{project_id}/documents", files=files)

    assert response.status_code == 200
    assert response.json()["uploaded_documents"][0]["filename"] == "plik.txt"
    mock_service.upload_project_documents.assert_awaited_once()

def test_invite_user_to_project(client, mock_service):
    project_id = uuid4()
    target_id = uuid4()
    membership = FakeMembership(target_id, "viewer")
    mock_service.invite_user_to_project.return_value = membership

    response = client.post(f"/projects/{project_id}/invite", params={"target_id": str(target_id), "role": "viewer"})
    assert response.status_code == 201
    assert response.json()["user_id"] == str(target_id)
    mock_service.invite_user_to_project.assert_called_once()

def test_update_user_role(client, mock_service):
    project_id = uuid4()
    target_id = uuid4()
    membership = FakeMembership(target_id, "owner")
    mock_service.update_user_role.return_value = membership

    response = client.put(f"/projects/{project_id}/members/{target_id}/role", params={"role": "owner"})
    assert response.status_code == 200
    assert response.json()["role"] == "owner"
    mock_service.update_user_role.assert_called_once()

def test_remove_user_from_project(client, mock_service):
    project_id = uuid4()
    target_id = uuid4()
    response = client.delete(f"/projects/{project_id}/members/{target_id}")
    assert response.status_code == 200
    mock_service.remove_user_from_project.assert_called_once()

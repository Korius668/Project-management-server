import pytest
from fastapi.testclient import TestClient
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


from fastapi.testclient import TestClient
import pytest
import uuid

from main import app

ROUTE = "/auth"
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def new_user(client):
    """Creates a test user and returns its credentials"""
    payload = {"login": "user_1", "password": "VerySafePass123"}
    response = client.post(f"{ROUTE}/sign_up", json=payload)
    assert response.status_code == 201
    return payload


class TestSignUp:
    def test_correct_input(self, client):
        payload = {"login": f"user_{uuid.uuid4().hex[:6]}", "password": "SafePass123"}
        response = client.post(f"{ROUTE}/sign_up", json=payload)
        assert response.status_code == 201

    def test_duplicate_signup(self, client):
        payload = {"login": f"user_{uuid.uuid4().hex[:6]}", "password": "SafePass123"}
        client.post(f"{ROUTE}/sign_up", json=payload)  # first attempt
        response = client.post(f"{ROUTE}/sign_up", json=payload)  # duplicate
        assert response.status_code == 400

class TestLogin:
    def test_login_existing_user(self, client, new_user):
        # precondition: signup was successful via fixture
        response = client.post(f"{ROUTE}/login", json=new_user)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
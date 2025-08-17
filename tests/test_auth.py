from fastapi.testclient import TestClient
import pytest
from main import app


client = TestClient(app)

ROUTE = "/auth"

@pytest.fixture
def new_user():
    """Creates a test user and returns its credentials"""
    payload = {"login": "user_1", "password": "VerySafePass123"}
    response = client.post(f"{ROUTE}/sign_up", json=payload)
    assert response.status_code == 201
    return payload


class TestSignUp:
    def test_correct_input(self):
        payload = {"login": "user_2", "password": "VerySafePass123"}
        response = client.post(f"{ROUTE}/sign_up", json=payload)
        assert response.status_code == 201

        # second attempt should fail
        response = client.post(f"{ROUTE}/sign_up", json=payload)
        assert response.status_code == 400


class TestLogin:
    def test_login_existing_user(self, new_user):
        # precondition: signup was successful via fixture
        response = client.post(f"{ROUTE}/login", json=new_user)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
"""End-to-end tests for authentication API."""

import pytest
from fastapi import status


class TestAuthenticationAPI:
    """Test authentication API endpoints end-to-end."""

    def test_create_user_success(self, test_client, sample_user_data):
        """Test successful user creation via API."""
        response = test_client.post("/auth/create_user", params=sample_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["email"] == sample_user_data["email"]
        assert data["name"] == sample_user_data["username"]
        assert "password" not in data  # Password should not be returned

    def test_create_user_duplicate_email_fails(self, test_client, sample_user_data):
        """Test that creating user with duplicate email fails."""
        # Create first user
        response1 = test_client.post("/auth/create_user", params=sample_user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create second user with same email
        duplicate_data = sample_user_data.copy()
        duplicate_data["username"] = "different_username"

        response2 = test_client.post("/auth/create_user", params=duplicate_data)

        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_user_duplicate_username_fails(self, test_client, sample_user_data):
        """Test that creating user with duplicate username fails."""
        # Create first user
        response1 = test_client.post("/auth/create_user", params=sample_user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to create second user with same username
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = "different@example.com"

        response2 = test_client.post("/auth/create_user", params=duplicate_data)

        assert response2.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_user_missing_parameters_fails(self, test_client):
        """Test that creating user with missing parameters fails."""
        response = test_client.post(
            "/auth/create_user",
            params={"username": "testuser"},  # Missing email and password
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_username_success(self, test_client, sample_user_data):
        """Test successful username via API."""
        # Create user first
        create_response = test_client.post("/auth/create_user", params=sample_user_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # username with email
        username_response = test_client.post(
            "/auth/login",
            params={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"],
            },
        )

        assert username_response.status_code == status.HTTP_200_OK
        data = username_response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_username_with_username_success(self, test_client, sample_user_data):
        """Test successful username with username via API."""
        # Create user first
        create_response = test_client.post("/auth/create_user", params=sample_user_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # username with username (note: current implementation uses email field for username)
        username_response = test_client.post(
            "/auth/login",
            params={
                "username": sample_user_data["username"],  # Using email as username
                "password": sample_user_data["password"],
            },
        )

        assert username_response.status_code == status.HTTP_200_OK

    def test_username_invalid_credentials_fails(self, test_client, sample_user_data):
        """Test username with invalid credentials fails."""
        # Create user first
        create_response = test_client.post("/auth/create_user", params=sample_user_data)
        assert create_response.status_code == status.HTTP_201_CREATED

        # Try username with wrong password
        username_response = test_client.post(
            "/auth/login",
            params={
                "username": sample_user_data["username"],
                "password": "wrongpassword",
            },
        )

        assert username_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in username_response.json()["detail"].lower()

    def test_username_nonexistent_user_fails(self, test_client):
        """Test username with non-existent user fails."""
        username_response = test_client.post(
            "/auth/login",
            params={"username": "nonexistent@example.com", "password": "somepassword"},
        )

        assert username_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_username_missing_parameters_fails(self, test_client):
        """Test username with missing parameters fails."""
        response = test_client.post(
            "/auth/login", params={"username": "test@example.com"}  # Missing password
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_complete_auth_flow(self, test_client, sample_user_data):
        """Test complete authentication flow: register -> username -> use token."""
        # Step 1: Register user
        register_response = test_client.post(
            "/auth/create_user", params=sample_user_data
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        user_data = register_response.json()

        # Step 2: username
        username_response = test_client.post(
            "/auth/login",
            params={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"],
            },
        )
        assert username_response.status_code == status.HTTP_200_OK
        token_data = username_response.json()

        # Step 3: Use token to access protected endpoint (create project)
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        project_response = test_client.post(
            "/projects/",
            json={"name": "Test Project", "description": "Test"},
            headers=headers,
        )
        print(headers)
        assert project_response.status_code == status.HTTP_201_CREATED
        project_data = project_response.json()
        assert project_data["name"] == "Test Project"


class TestAuthenticationSecurity:
    """Test authentication security aspects."""

    def test_access_protected_endpoint_without_token_fails(self, test_client):
        """Test accessing protected endpoint without token fails."""
        response = test_client.post(
            "/projects/", json={"name": "Test Project", "description": "Test"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_invalid_token_fails(self, test_client):
        """Test accessing protected endpoint with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = test_client.post(
            "/projects/",
            json={"name": "Test Project", "description": "Test"},
            headers=headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_malformed_header_fails(self, test_client):
        """Test accessing protected endpoint with malformed auth header fails."""
        headers = {"Authorization": "InvalidFormat token_here"}
        response = test_client.post(
            "/projects/",
            json={"name": "Test Project", "description": "Test"},
            headers=headers,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_not_returned_in_responses(self, test_client, sample_user_data):
        """Test that password is never returned in API responses."""
        # Create user
        response = test_client.post("/auth/create_user", params=sample_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Ensure password fields are not in response
        assert "password" not in data
        assert "password_hash" not in data
        assert sample_user_data["password"] not in str(data)

"""End-to-end tests for projects API."""

import pytest
from fastapi import status
import uuid


class TestProjectsAPI:
    """Test projects API endpoints end-to-end."""

    def test_create_project_success(
        self, test_client, authenticated_user, sample_project_data
    ):
        """Test successful project creation via API."""
        response = test_client.post(
            "/projects/",
            json=sample_project_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        assert "created_at" in data

    def test_create_project_without_auth_fails(self, test_client, sample_project_data):
        """Test creating project without authentication fails."""
        response = test_client.post("/projects/", json=sample_project_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_project_missing_name_fails(self, test_client, authenticated_user):
        """Test creating project without name fails."""
        response = test_client.post(
            "/projects/",
            json={"description": "Project without name"},
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_project_success(self, test_client, authenticated_user, test_project):
        """Test getting project via API."""
        response = test_client.get(
            f"/projects/{test_project['id']}", headers=authenticated_user["headers"]
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_project["id"]
        assert data["name"] == test_project["name"]

    def test_get_project_without_auth_fails(self, test_client, test_project):
        """Test getting project without authentication fails."""
        response = test_client.get(f"/projects/{test_project['id']}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_nonexistent_project_fails(self, test_client, authenticated_user):
        """Test getting non-existent project fails."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(
            f"/projects/{fake_id}", headers=authenticated_user["headers"]
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_project_info_success(
        self, test_client, authenticated_user, test_project
    ):
        """Test getting detailed project info via API."""
        response = test_client.get(
            f"/projects/{test_project['id']}/info",
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "project" in data
        assert "members" in data
        assert "documents" in data

    def test_update_project_success(
        self, test_client, authenticated_user, test_project
    ):
        """Test updating project via API."""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description",
        }

        response = test_client.put(
            f"/projects/{test_project['id']}/info",
            json=update_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Project Name"
        assert data["description"] == "Updated description"

    def test_update_project_partial_success(
        self, test_client, authenticated_user, test_project
    ):
        """Test partial project update via API."""
        update_data = {"name": "Only Name Updated"}

        response = test_client.put(
            f"/projects/{test_project['id']}/info",
            json=update_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Only Name Updated"
        # Description should remain unchanged
        assert data["description"] == test_project["description"]

    def test_delete_project_success(
        self, test_client, authenticated_user, test_project
    ):
        """Test deleting project via API."""
        response = test_client.delete(
            f"/projects/{test_project['id']}", headers=authenticated_user["headers"]
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

        # Verify project is deleted
        get_response = test_client.get(
            f"/projects/{test_project['id']}", headers=authenticated_user["headers"]
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestProjectMembership:
    """Test project membership management via API."""

    @pytest.fixture
    def second_user(self, test_client):
        """Create a second user for membership tests."""
        user_data = {
            "username": f"seconduser_{uuid.uuid4().hex[:8]}",
            "email": f"second_{uuid.uuid4().hex[:8]}@example.com",
            "password": "password123",
        }

        # Create user
        response = test_client.post("/auth/create_user", params=user_data)
        assert response.status_code == 201
        user = response.json()

        # Login to get token
        login_response = test_client.post(
            "/auth/login",
            params={
                "username": user_data["username"],
                "password": user_data["password"],
            },
        )
        assert login_response.status_code == 200
        token_data = login_response.json()

        return {
            "user": user,
            "token": token_data["access_token"],
            "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
        }

    def test_invite_user_to_project_success(
        self, test_client, authenticated_user, test_project, second_user
    ):
        """Test inviting user to project via API."""
        response = test_client.post(
            f"/projects/{test_project['id']}/invite",
            params={"target_id": second_user["user"]["id"], "role": "editor"},
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == second_user["user"]["id"]
        assert data["role"] == "editor"

    def test_invite_user_without_permission_fails(
        self, test_client, second_user, test_project
    ):
        """Test that non-owner cannot invite users."""
        # Try to invite as non-owner
        response = test_client.post(
            f"/projects/{test_project['id']}/invite",
            params={"target_id": str(uuid.uuid4()), "role": "viewer"},
            headers=second_user["headers"],
        )

        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_update_user_role_success(
        self, test_client, authenticated_user, test_project, second_user
    ):
        """Test updating user role in project via API."""
        # First invite user
        invite_response = test_client.post(
            f"/projects/{test_project['id']}/invite",
            params={"target_id": second_user["user"]["id"], "role": "viewer"},
            headers=authenticated_user["headers"],
        )
        assert invite_response.status_code == status.HTTP_201_CREATED

        # Update role
        response = test_client.put(
            f"/projects/{test_project['id']}/members/{second_user['user']['id']}/role",
            params={"role": "editor"},
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "editor"


class TestProjectDocuments:
    """Test project document management via API."""

    def test_upload_documents_without_permission_fails(
        self, test_client, test_project, sample_file_content
    ):
        """Test uploading documents without authentication fails."""
        files = [("files", ("test.txt", sample_file_content, "text/plain"))]

        response = test_client.post(
            f"/projects/{test_project['id']}/documents", files=files
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProjectPermissions:
    """Test project permission system via API."""

    def test_owner_can_access_all_operations(
        self, test_client, authenticated_user, test_project
    ):
        """Test that project owner can perform all operations."""
        project_id = test_project["id"]
        headers = authenticated_user["headers"]

        # Can read project
        response = test_client.get(f"/projects/{project_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK

        # Can update project
        response = test_client.put(
            f"/projects/{project_id}/info",
            json={"name": "Updated Name"},
            headers=headers,
        )
        assert response.status_code == status.HTTP_200_OK

        # Can delete project
        response = test_client.delete(f"/projects/{project_id}", headers=headers)
        assert response.status_code == status.HTTP_200_OK

    def test_non_member_cannot_access_project(self, test_client, test_project):
        """Test that non-member cannot access project."""
        # Create another user
        other_user_data = {
            "username": f"otheruser_{uuid.uuid4().hex[:8]}",
            "email": f"other_{uuid.uuid4().hex[:8]}@example.com",
            "password": "password123",
        }

        create_response = test_client.post("/auth/create_user", params=other_user_data)
        assert create_response.status_code == 201

        login_response = test_client.post(
            "/auth/login",
            params={
                "username": other_user_data["username"],
                "password": other_user_data["password"],
            },
        )
        assert login_response.status_code == 200

        other_headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        # Try to access project
        response = test_client.get(
            f"/projects/{test_project['id']}", headers=other_headers
        )

        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

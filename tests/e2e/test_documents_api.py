"""End-to-end tests for documents API."""
import pytest
from fastapi import status
import uuid
from io import BytesIO


class TestDocumentsAPI:
    """Test documents API endpoints end-to-end."""

    def test_upload_document_success(self, test_client, authenticated_user, test_project, sample_file_content):
        """Test successful document upload via API."""
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {
            "project_id": test_project["id"],
            "name": "Test Document",
            "description": "A test document"
        }
        
        response = test_client.post(
            "/documents/",
            files=files,
            data=data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        doc_data = response.json()
        assert "id" in doc_data
        assert doc_data["filename"] == "Test Document"
        assert doc_data["content_type"] == "text/plain"
        assert doc_data["size_bytes"] > 0

    def test_upload_document_without_auth_fails(self, test_client, test_project, sample_file_content):
        """Test uploading document without authentication fails."""
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {"project_id": test_project["id"]}
        
        response = test_client.post(
            "/documents/",
            files=files,
            data=data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_document_missing_file_fails(self, test_client, authenticated_user, test_project):
        """Test uploading document without file fails."""
        data = {"project_id": test_project["id"]}
        
        response = test_client.post(
            "/documents/",
            data=data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_document_missing_project_id_fails(self, test_client, authenticated_user, sample_file_content):
        """Test uploading document without project ID fails."""
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        
        response = test_client.post(
            "/documents/",
            files=files,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_download_document_success(self, test_client, authenticated_user, test_project, sample_file_content):
        """Test successful document download via API."""
        # First upload a document
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {"project_id": test_project["id"]}
        
        upload_response = test_client.post(
            "/documents/",
            files=files,
            data=data,
            headers=authenticated_user["headers"]
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        doc_data = upload_response.json()
        
        # Download the document
        download_response = test_client.get(
            f"/documents/{doc_data['id']}",
            headers=authenticated_user["headers"]
        )
        
        assert download_response.status_code == status.HTTP_200_OK
        assert download_response.content == sample_file_content

    def test_download_document_without_auth_fails(self, test_client, authenticated_user, test_project, sample_file_content):
        """Test downloading document without authentication fails."""
        # First upload a document
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {"project_id": test_project["id"]}
        
        upload_response = test_client.post(
            "/documents/",
            files=files,
            data=data,
            headers=authenticated_user["headers"]
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        doc_data = upload_response.json()
        
        # Try to download without auth
        download_response = test_client.get(f"/documents/{doc_data['id']}")
        
        assert download_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_download_nonexistent_document_fails(self, test_client, authenticated_user):
        """Test downloading non-existent document fails."""
        fake_id = str(uuid.uuid4())
        
        response = test_client.get(
            f"/documents/{fake_id}",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_document_success(self, test_client, authenticated_user, test_project, sample_file_content):
        """Test successful document update via API."""
        # First upload a document
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {"project_id": test_project["id"]}
        
        upload_response = test_client.post(
            "/documents/",
            files=files,
            data=data,
            headers=authenticated_user["headers"]
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        doc_data = upload_response.json()
        
        # Update the document
        update_data = {
            "filename": "updated_test.txt",
            "metadata": {"updated": True, "version": 2}
        }
        
        update_response = test_client.put(
            f"/documents/{doc_data['id']}",
            json=update_data,
            headers=authenticated_user["headers"]
        )
        
        assert update_response.status_code == status.HTTP_200_OK
        updated_doc = update_response.json()
        assert updated_doc["filename"] == "updated_test.txt"

    def test_update_document_partial_success(self, test_client, authenticated_user, test_project, sample_file_content):
        """Test partial document update via API."""
        # First upload a document
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {"project_id": test_project["id"]}
        
        upload_response = test_client.post(
            "/documents/",
            files=files,
            data=data,
            headers=authenticated_user["headers"]
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        doc_data = upload_response.json()
        
        # Update only filename
        update_data = {"filename": "only_filename_updated.txt"}
        
        update_response = test_client.put(
            f"/documents/{doc_data['id']}",
            json=update_data,
            headers=authenticated_user["headers"]
        )
        
        assert update_response.status_code == status.HTTP_200_OK
        updated_doc = update_response.json()
        assert updated_doc["filename"] == "only_filename_updated.txt"

    def test_delete_document_success(self, test_client, authenticated_user, test_project, sample_file_content):
        """Test successful document deletion via API."""
        # First upload a document
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {"project_id": test_project["id"]}
        
        upload_response = test_client.post(
            "/documents/",
            files=files,
            data=data,
            headers=authenticated_user["headers"]
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        doc_data = upload_response.json()
        
        # Delete the document
        delete_response = test_client.delete(
            f"/documents/{doc_data['id']}",
            headers=authenticated_user["headers"]
        )
        
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify document is deleted
        get_response = test_client.get(
            f"/documents/{doc_data['id']}",
            headers=authenticated_user["headers"]
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_document_without_auth_fails(self, test_client, authenticated_user, test_project, sample_file_content):
        """Test deleting document without authentication fails."""
        # First upload a document
        files = {"file": ("test.txt", sample_file_content, "text/plain")}
        data = {"project_id": test_project["id"]}
        
        upload_response = test_client.post(
            "/documents/",
            files=files,
            data=data,
            headers=authenticated_user["headers"]
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        doc_data = upload_response.json()
        
        # Try to delete without auth
        delete_response = test_client.delete(f"/documents/{doc_data['id']}")
        
        assert delete_response.status_code == status.HTTP_401_UNAUTHORIZED

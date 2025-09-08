import pytest
from unittest.mock import Mock

from uuid import uuid4
from app.usecases.documents import DocumentsService
from app.domain.models import Document, User, ProjectRole, Project, ProjectMembership
from app.domain.exceptions import DocumentNotFoundError, InsufficientPermissionsError


@pytest.fixture
def documents_service(
    mock_documents_repository, mock_memberships_repository, mock_file_storage
):
    return DocumentsService(
        documents_repo=mock_documents_repository,
        memberships_repo=mock_memberships_repository,
        file_storage=mock_file_storage,
    )


class TestUploadDocument:

    @pytest.mark.asyncio  # Added async marker for pytest
    async def test_success(
        self,
        documents_service,
        mock_documents_repository,
        mock_memberships_repository,
        mock_file_storage,
        user1,
        membership1,
        mock_upload_file1,
        document1,
        filemetadata1,
    ):

        mock_memberships_repository.get.return_value = membership1  # Fixed fixture name
        mock_file_storage.save_file.return_value = filemetadata1
        mock_documents_repository.add.return_value = document1

        # When
        result = await documents_service.upload_document(  # Added await
            project_id=document1.project_id, user_id=user1.id, file=mock_upload_file1
        )

        # Then
        assert isinstance(
            result, Document
        )  # Service returns Document, not DocumentResponse
        assert result.filename == document1.filename
        assert result.content_type == document1.content_type
        assert result.size_bytes == document1.size_bytes

        mock_file_storage.save_file.assert_called_once()
        mock_documents_repository.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_insufficient_permissions(
        self,
        documents_service,
        mock_memberships_repository,
        user1,
        mock_upload_file1,
        project1,
    ):
        # Given
        membership = Mock()
        membership.role = ProjectRole.viewer
        mock_memberships_repository.get.return_value = membership

        # When/Then
        with pytest.raises(InsufficientPermissionsError):  # Fixed exception name
            await documents_service.upload_document(
                project1.id, user1.id, mock_upload_file1
            )

    @pytest.mark.asyncio  # Added async marker
    async def test_success(
        self,
        documents_service,
        mock_documents_repository,
        mock_memberships_repository,
        mock_file_storage,
        user1,
        document1,
        membership1,
    ):
        # Given
        mock_memberships_repository.get.return_value = membership1
        mock_documents_repository.get.return_value = document1

        # When
        await documents_service.delete_document(document1.id, user1.id)  # Added await

        # Then
        mock_file_storage.delete_file.assert_called_once_with(document1.storage_path)
        mock_documents_repository.delete.assert_called_once_with(document1.id)

    @pytest.mark.asyncio
    async def test_document_not_found(
        self, documents_service, mock_documents_repository, user1
    ):
        # Given
        mock_documents_repository.get.return_value = None

        # When/Then
        with pytest.raises(DocumentNotFoundError):  # Fixed exception name
            await documents_service.delete_document(uuid4(), user1.id)

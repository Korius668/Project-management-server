import pytest
from unittest.mock import Mock, AsyncMock
from uuid import uuid4
from fastapi import UploadFile
from typing import BinaryIO
from app.usecases.documents import DocumentsService
from app.domain.models import Document


class TestDocumentsService:
    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def documents_service(self, mock_repository):
        return DocumentsService(mock_repository)

    @pytest.fixture
    def sample_document(self):
        return (
            Document(
                id=uuid4(),
                filename="test0.pdf",
                project_id=uuid4(),
                content_type="pdf",
                size_bytes=20,
                storage_path="/path0",
            ),
        )

    @pytest.fixture
    def mock_upload_file(self):
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.pdf"
        mock_file.content_type = "application/pdf"
        return mock_file

    @pytest.mark.asyncio
    async def test_upload_document_success(
        self, documents_service, mock_repository, mock_upload_file, sample_document
    ):
        """Test successful document upload."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()
        name = "Test Document"
        description = "Test description"

        mock_repository.upload_document = AsyncMock(return_value=sample_document)

        # Act
        result = await documents_service.upload_document(
            project_id, user_id, mock_upload_file, name, description
        )

        # Assert
        mock_repository.upload_document.assert_called_once_with(
            project_id, user_id, mock_upload_file, name, description
        )
        assert result == sample_document

    @pytest.mark.asyncio
    async def test_upload_document_without_optional_params(
        self, documents_service, mock_repository, mock_upload_file, sample_document
    ):
        """Test document upload without optional name and description."""
        # Arrange
        project_id = uuid4()
        user_id = uuid4()

        mock_repository.upload_document = AsyncMock(return_value=sample_document)

        # Act
        result = await documents_service.upload_document(
            project_id, user_id, mock_upload_file
        )

        # Assert
        mock_repository.upload_document.assert_called_once_with(
            project_id, user_id, mock_upload_file, None, None
        )
        assert result == sample_document

    @pytest.mark.asyncio
    async def test_download_document_success(
        self, documents_service, mock_repository, sample_document
    ):
        """Test successful document download."""
        # Arrange
        document_id = uuid4()
        user_id = uuid4()
        file = BinaryIO()
        mock_repository.download_document = AsyncMock(return_value=file)

        # Act
        result = await documents_service.download_document(document_id, user_id)

        # Assert
        mock_repository.download_document.assert_called_once_with(document_id, user_id)
        assert result == file

    def test_update_document_success(
        self, documents_service, mock_repository, sample_document
    ):
        """Test successful document metadata update."""
        # Arrange
        document_id = uuid4()
        user_id = uuid4()
        filename = "updated_file.pdf"
        metadata = {"updated": True, "version": 2}

        mock_repository.update_document.return_value = sample_document

        # Act
        result = documents_service.update_document(
            document_id, user_id, filename, metadata
        )

        # Assert
        mock_repository.update_document.assert_called_once_with(
            document_id, user_id, filename, metadata
        )
        assert result == sample_document

    def test_update_document_partial_update(
        self, documents_service, mock_repository, sample_document
    ):
        """Test document update with only filename."""
        # Arrange
        document_id = uuid4()
        user_id = uuid4()
        filename = "new_name.pdf"

        mock_repository.update_document.return_value = sample_document

        # Act
        result = documents_service.update_document(
            document_id, user_id, filename=filename
        )

        # Assert
        mock_repository.update_document.assert_called_once_with(
            document_id, user_id, filename, None
        )
        assert result == sample_document

    @pytest.mark.asyncio
    async def test_delete_document_success(self, documents_service, mock_repository):
        """Test successful document deletion."""
        # Arrange
        document_id = uuid4()
        user_id = uuid4()

        mock_repository.delete_document = AsyncMock(return_value=None)

        # Act
        result = await documents_service.delete_document(document_id, user_id)

        # Assert
        mock_repository.delete_document.assert_called_once_with(document_id, user_id)
        assert result is None

    def test_documents_service_initialization(self, mock_repository):
        """Test DocumentsService initialization with repository."""
        # Act
        service = DocumentsService(mock_repository)

        # Assert
        assert service.repository == mock_repository

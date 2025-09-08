import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from io import BytesIO

from app.adapters.file_storage.local_storage import LocalFileStorageAdapter
from app.domain.exceptions import DocumentNotFoundError


class TestLocalFileStorageAdapter:

    @pytest.fixture
    def temp_storage_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def file_storage(self, temp_storage_dir):
        return LocalFileStorageAdapter(base_path=temp_storage_dir)

    @pytest.fixture
    def mock_file_content(self):
        content = b"test file content"
        file_obj = BytesIO(content)
        file_obj.read = AsyncMock(return_value=content)
        return file_obj

    @pytest.mark.asyncio
    async def test_save_file_success(self, file_storage, mock_file_content):
        # When
        result = await file_storage.save_file(
            file_content=mock_file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id=123,
        )

        # Then
        assert result.filename == "test.txt"
        assert result.content_type == "text/plain"
        assert result.size_bytes == 17
        assert "project-123" in result.storage_path
        assert result.storage_path.endswith(".txt")

        # Verify file exists
        full_path = Path(file_storage.base_path) / result.storage_path
        assert full_path.exists()

    @pytest.mark.asyncio
    async def test_save_file_creates_directory(self, file_storage, mock_file_content):
        # When
        await file_storage.save_file(
            file_content=mock_file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id=456,
        )

        # Then
        project_dir = Path(file_storage.base_path) / "project-456"
        assert project_dir.exists()
        assert project_dir.is_dir()

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_storage, mock_file_content):
        # Given
        result = await file_storage.save_file(
            file_content=mock_file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id=123,
        )

        # When
        deleted = await file_storage.delete_file(result.storage_path)

        # Then
        assert deleted is True
        full_path = Path(file_storage.base_path) / result.storage_path
        assert not full_path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_returns_false(self, file_storage):
        # When
        result = await file_storage.delete_file("nonexistent/file.txt")

        # Then
        assert result is False

    @pytest.mark.asyncio
    async def test_get_file_success(self, file_storage, mock_file_content):
        # Given
        result = await file_storage.save_file(
            file_content=mock_file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id=123,
        )

        # When
        file_obj = await file_storage.get_file(result.storage_path)

        # Then
        assert file_obj is not None
        file_obj.close()  # Clean up

    @pytest.mark.asyncio
    async def test_get_nonexistent_file_raises_error(self, file_storage):
        # When/Then
        with pytest.raises(DocumentNotFoundError, match="File not found"):
            await file_storage.get_file("nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_file_exists_returns_true_for_existing_file(
        self, file_storage, mock_file_content
    ):
        # Given
        result = await file_storage.save_file(
            file_content=mock_file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id=123,
        )

        # When/Then
        exists = await file_storage.file_exists(result.storage_path)
        assert exists is True

    @pytest.mark.asyncio
    async def test_file_exists_returns_false_for_nonexistent_file(self, file_storage):
        # When/Then
        exists = await file_storage.file_exists("nonexistent/file.txt")
        assert exists is False

    @pytest.mark.asyncio
    async def test_get_file_url_returns_correct_path(self, file_storage):
        # When
        url = await file_storage.get_file_url("project-123/test-file.txt")

        # Then
        assert url == "/files/project-123/test-file.txt"

    @pytest.mark.asyncio
    async def test_save_file_with_metadata(self, file_storage, mock_file_content):
        # Given
        metadata = {"description": "Test document", "tags": ["test"]}

        # When
        result = await file_storage.save_file(
            file_content=mock_file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id=123,
            metadata=metadata,
        )

        # Then
        assert result.metadata == metadata

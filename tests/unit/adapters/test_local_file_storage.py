import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from unittest.mock import Mock, patch
from app.adapters.repositories.file_storage.local_storage import LocalFileStorageAdapter
from app.ports.repositories import FileMetadata
from app.domain.exceptions import DocumentNotFoundError


class TestLocalFileStorageAdapter:
    """Test cases for LocalFileStorageAdapter."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    @pytest.fixture
    def file_storage(self, temp_dir):
        """Create a LocalFileStorageAdapter instance for testing."""
        return LocalFileStorageAdapter(base_path=temp_dir)

    @pytest.mark.asyncio
    async def test_save_file_success(self, file_storage):
        """Test successful file saving."""
        file_content = BytesIO(b"This is test file content")

        result = await file_storage.save_file(
            file_content=file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id="1",
            metadata={"description": "Test file"},
        )

        assert isinstance(result, FileMetadata)
        assert result.filename == "test.txt"
        assert result.content_type == "text/plain"
        assert result.size_bytes == len(b"This is test file content")
        assert "project-1" in result.storage_path
        assert result.metadata == {"description": "Test file"}

    @pytest.mark.asyncio
    async def test_save_file_creates_project_directory(self, file_storage):
        """Test that project directory is created when saving file."""
        file_content = BytesIO(b"Test content")
        project_id = "123"

        await file_storage.save_file(
            file_content=file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id=project_id,
        )

        project_dir = file_storage.base_path / f"project-{project_id}"
        assert project_dir.exists()
        assert project_dir.is_dir()

    @pytest.mark.asyncio
    async def test_save_file_generates_unique_filename(self, file_storage):
        """Test that unique filenames are generated to avoid conflicts."""
        file_content1 = BytesIO(b"Content 1")
        file_content2 = BytesIO(b"Content 2")

        result1 = await file_storage.save_file(
            file_content=file_content1,
            filename="test.txt",
            content_type="text/plain",
            project_id="1",
        )

        result2 = await file_storage.save_file(
            file_content=file_content2,
            filename="test.txt",
            content_type="text/plain",
            project_id="1",
        )

        assert result1.storage_path != result2.storage_path

    @pytest.mark.asyncio
    async def test_get_file_success(self, file_storage):
        """Test successful file retrieval."""
        # First save a file
        file_content = BytesIO(b"Test content for retrieval")
        result = await file_storage.save_file(
            file_content=file_content,
            filename="retrieve_test.txt",
            content_type="text/plain",
            project_id="1",
        )

        # Then retrieve it
        retrieved_file = await file_storage.get_file(result.storage_path)
        retrieved_content = retrieved_file.read()
        retrieved_file.close()

        assert retrieved_content == b"Test content for retrieval"

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, file_storage):
        """Test file retrieval when file doesn't exist."""
        with pytest.raises(DocumentNotFoundError):
            await file_storage.get_file("nonexistent/path.txt")

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_storage):
        """Test successful file deletion."""
        # First save a file
        file_content = BytesIO(b"Content to delete")
        result = await file_storage.save_file(
            file_content=file_content,
            filename="delete_test.txt",
            content_type="text/plain",
            project_id="1",
        )

        # Verify file exists
        assert await file_storage.file_exists(result.storage_path)

        # Delete the file
        deleted = await file_storage.delete_file(result.storage_path)

        assert deleted is True
        assert not await file_storage.file_exists(result.storage_path)

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, file_storage):
        """Test file deletion when file doesn't exist."""
        deleted = await file_storage.delete_file("nonexistent/path.txt")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_file_exists_true(self, file_storage):
        """Test file_exists returns True for existing file."""
        # Save a file
        file_content = BytesIO(b"Existence test content")
        result = await file_storage.save_file(
            file_content=file_content,
            filename="exists_test.txt",
            content_type="text/plain",
            project_id="1",
        )

        exists = await file_storage.file_exists(result.storage_path)
        assert exists is True

    @pytest.mark.asyncio
    async def test_file_exists_false(self, file_storage):
        """Test file_exists returns False for non-existing file."""
        exists = await file_storage.file_exists("nonexistent/path.txt")
        assert exists is False

    @pytest.mark.asyncio
    async def test_get_file_url(self, file_storage):
        """Test file URL generation."""
        storage_path = "project-1/test-file.txt"
        url = await file_storage.get_file_url(storage_path)

        assert url == f"/files/{storage_path}"

    @pytest.mark.asyncio
    async def test_get_file_url_with_expiry(self, file_storage):
        """Test file URL generation with custom expiry."""
        storage_path = "project-1/test-file.txt"
        url = await file_storage.get_file_url(storage_path, expires_in=7200)

        # For local storage, expiry doesn't affect the URL
        assert url == f"/files/{storage_path}"

    @pytest.mark.asyncio
    async def test_save_file_preserves_extension(self, file_storage):
        """Test that file extension is preserved in unique filename."""
        file_content = BytesIO(b"PDF content")
        result = await file_storage.save_file(
            file_content=file_content,
            filename="document.pdf",
            content_type="application/pdf",
            project_id="1",
        )

        # The storage path should contain a UUID filename with .pdf extension
        assert result.storage_path.endswith(".pdf")
        assert "project-1" in result.storage_path

    @pytest.mark.asyncio
    async def test_save_file_handles_no_extension(self, file_storage):
        """Test saving file with no extension."""
        file_content = BytesIO(b"No extension content")
        result = await file_storage.save_file(
            file_content=file_content,
            filename="README",
            content_type="text/plain",
            project_id="1",
        )

        assert isinstance(result, FileMetadata)
        assert result.filename == "README"
        # Storage path should not have an extension since original didn't
        assert not result.storage_path.split("/")[-1].endswith(".")

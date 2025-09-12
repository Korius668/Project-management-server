"""Integration tests for file storage."""
import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO

from app.adapters.repositories.file_storage.local_storage import LocalFileStorageAdapter
from app.domain.exceptions import DocumentNotFoundError


class TestLocalFileStorageAdapter:
    """Test local file storage adapter integration."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def file_storage(self, temp_storage_path):
        """Create file storage adapter with temp path."""
        return LocalFileStorageAdapter(str(temp_storage_path))

    @pytest.mark.asyncio
    async def test_save_file_success(self, file_storage):
        """Test successful file saving."""
        file_content = BytesIO(b"This is test file content")
        
        result = await file_storage.save_file(
            file_content=file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id="1",
            metadata={"description": "Test file"}
        )
        
        assert result is not None
        assert result.filename == "test.txt"
        assert result.content_type == "text/plain"
        assert result.size_bytes == len(b"This is test file content")
        assert "project-1" in result.storage_path
        assert result.metadata == {"description": "Test file"}

    @pytest.mark.asyncio
    async def test_save_file_creates_project_directory(self, file_storage, temp_storage_path):
        """Test that saving file creates project directory."""
        file_content = BytesIO(b"test content")
        
        await file_storage.save_file(
            file_content=file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id="123"
        )
        
        project_dir = temp_storage_path / "project-123"
        assert project_dir.exists()
        assert project_dir.is_dir()

    @pytest.mark.asyncio
    async def test_save_file_generates_unique_filename(self, file_storage):
        """Test that saving files generates unique filenames."""
        file_content1 = BytesIO(b"content 1")
        file_content2 = BytesIO(b"content 2")
        
        result1 = await file_storage.save_file(
            file_content=file_content1,
            filename="test.txt",
            content_type="text/plain",
            project_id="1"
        )
        
        result2 = await file_storage.save_file(
            file_content=file_content2,
            filename="test.txt",  # Same filename
            content_type="text/plain",
            project_id="1"
        )
        
        # Storage paths should be different (unique UUIDs)
        assert result1.storage_path != result2.storage_path
        # But original filenames should be preserved
        assert result1.filename == "test.txt"
        assert result2.filename == "test.txt"

    @pytest.mark.asyncio
    async def test_get_file_success(self, file_storage):
        """Test successful file retrieval."""
        # Save file first
        original_content = b"This is test file content"
        file_content = BytesIO(original_content)
        
        save_result = await file_storage.save_file(
            file_content=file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id="1"
        )
        
        # Get file
        retrieved_file = await file_storage.get_file(save_result.storage_path)
        
        assert retrieved_file is not None
        retrieved_content = retrieved_file.read()
        assert retrieved_content == original_content

    @pytest.mark.asyncio
    async def test_get_file_not_found_raises_error(self, file_storage):
        """Test getting non-existent file raises error."""
        with pytest.raises(DocumentNotFoundError, match="File not found"):
            await file_storage.get_file("nonexistent/path.txt")

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_storage, temp_storage_path):
        """Test successful file deletion."""
        # Save file first
        file_content = BytesIO(b"test content")
        save_result = await file_storage.save_file(
            file_content=file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id="1"
        )
        
        # Verify file exists
        file_path = temp_storage_path / save_result.storage_path
        assert file_path.exists()
        
        # Delete file
        result = await file_storage.delete_file(save_result.storage_path)
        
        assert result is True
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_returns_false(self, file_storage):
        """Test deleting non-existent file returns False."""
        result = await file_storage.delete_file("nonexistent/path.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_file_exists_success(self, file_storage):
        """Test checking file existence."""
        # Save file first
        file_content = BytesIO(b"test content")
        save_result = await file_storage.save_file(
            file_content=file_content,
            filename="test.txt",
            content_type="text/plain",
            project_id="1"
        )
        
        # Check existence
        exists = await file_storage.file_exists(save_result.storage_path)
        assert exists is True
        
        # Check non-existent file
        not_exists = await file_storage.file_exists("nonexistent/path.txt")
        assert not_exists is False

    @pytest.mark.asyncio
    async def test_get_file_url_returns_path(self, file_storage):
        """Test getting file URL returns path."""
        storage_path = "project-1/test.txt"
        
        url = await file_storage.get_file_url(storage_path)
        
        assert url == "/files/project-1/test.txt"


    @pytest.mark.asyncio
    async def test_save_file_preserves_extension(self, file_storage):
        """Test that file extension is preserved in storage path."""
        file_content = BytesIO(b"test content")
        
        result = await file_storage.save_file(
            file_content=file_content,
            filename="document.pdf",
            content_type="application/pdf",
            project_id="1"
        )
        
        assert result.storage_path.endswith(".pdf")
        assert result.filename == "document.pdf"
        assert result.content_type == "application/pdf"

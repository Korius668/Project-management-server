import uuid
import aiofiles
from pathlib import Path
from typing import BinaryIO, Optional
from io import BytesIO
from app.ports.repositories import FileStoragePort, FileMetadata
from app.domain.exceptions import DocumentNotFoundError
from app.config import secrets


class LocalFileStorageAdapter(FileStoragePort):
    """Local file system adapter - defines HOW we store files locally"""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or secrets.file_storage_path)
        self.base_path.mkdir(exist_ok=True)

    
    async def save_file(
        self,
        file_content: BinaryIO,
        filename: str,
        content_type: str,
        project_id: str,
        metadata: Optional[dict] = None,
    ) -> FileMetadata:
        # Create project directory
        project_dir = self.base_path / f"project-{project_id}"
        project_dir.mkdir(exist_ok=True)

        # Generate unique filename to avoid conflicts
        file_extension = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = project_dir / unique_filename

        file_content.seek(0)  # Ensure we're at the beginning
        content = file_content.read()  # Remove await here - BytesIO.read() is synchronous
        
        if len(content) > secrets.max_file_size_mb * 1024 * 1024:
            raise ValueError(
                f"File size exceeds maximum allowed size of {secrets.max_file_size_mb}MB"
            )

        # Save file content asynchronously
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Calculate actual file size
        actual_size = file_path.stat().st_size

        return FileMetadata(
            filename=filename,
            content_type=content_type,
            size_bytes=actual_size,
            storage_path=str(file_path.relative_to(self.base_path)),
            metadata=metadata or {},
        )

    async def get_file(self, storage_path: str):
        file_path = self.base_path / storage_path
        if not file_path.exists():
            raise DocumentNotFoundError(f"File not found: {storage_path}")

        async with aiofiles.open(file_path, "rb") as f:
            content = await f.read()
        return BytesIO(content)

    async def delete_file(self, storage_path: str) -> bool:
        file_path = self.base_path / storage_path
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    async def file_exists(self, storage_path: str) -> bool:
        file_path = self.base_path / storage_path
        return file_path.exists()

    async def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        # For local storage, return a simple file path
        # In production, you might want to serve files through a web server
        return f"/files/{storage_path}"

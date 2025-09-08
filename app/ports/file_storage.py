from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from dataclasses import dataclass


@dataclass
class FileMetadata:
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    metadata: Optional[dict] = None


class FileStoragePort(ABC):
    """Port for file storage operations - defines WHAT we can do with files"""

    @abstractmethod
    async def save_file(
        self,
        file_content: BinaryIO,
        filename: str,
        content_type: str,
        project_id: int,
        metadata: Optional[dict] = None,
    ) -> FileMetadata:
        """Save file and return metadata with storage path"""
        pass

    @abstractmethod
    async def get_file(self, storage_path: str) -> BinaryIO:
        """Retrieve file content by storage path"""
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file by storage path"""
        pass

    @abstractmethod
    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists at storage path"""
        pass

    @abstractmethod
    async def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get temporary URL for file access (useful for cloud storage)"""
        pass

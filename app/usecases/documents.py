from uuid import UUID
from typing import Optional, Dict, Any, BinaryIO
from app.domain.models import Document
from fastapi import UploadFile
from app.ports.head_repository import Repository


class DocumentsService:
    def __init__(self, repository: Repository):
        self.repository = repository

    async def upload_document(
        self,
        project_id: UUID,
        user_id: UUID,
        file: UploadFile,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Document:
        """Upload a new document to a project."""
        return await self.repository.upload_document(
            project_id, user_id, file, name, description
        )

    async def download_document(self, document_id: UUID, user_id: UUID) -> BinaryIO:
        """Download a document if user has access to the project."""

        return await self.repository.download_document(document_id, user_id)

    def update_document(
        self,
        document_id: UUID,
        user_id: UUID,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Update document metadata if user has editor/owner permissions."""

        return self.repository.update_document(document_id, user_id, filename, metadata)

    async def delete_document(self, document_id: UUID, user_id: UUID) -> None:
        """Delete a document if user has editor/owner permissions."""
        await self.repository.delete_document(document_id, user_id)

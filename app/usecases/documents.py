from uuid import UUID
from typing import List, Optional, Dict, Any
from app.domain.models import Document, ProjectRole
from app.domain.exceptions import DocumentNotFoundError, InsufficientPermissionsError
from app.ports.repositories import DocumentsRepository, ProjectMembershipsRepository
from app.ports.file_storage import FileStoragePort
from fastapi import UploadFile


class DocumentsService:
    def __init__(
        self,
        documents_repo: DocumentsRepository,
        memberships_repo: ProjectMembershipsRepository,
        file_storage: FileStoragePort,
    ):
        self.documents_repo = documents_repo
        self.memberships_repo = memberships_repo
        self.file_storage = file_storage

    async def upload_document(
        self,
        project_id: UUID,
        user_id: UUID,
        file: UploadFile,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Document:
        """Upload a new document to a project."""
        membership = self.memberships_repo.get(project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can upload documents"
            )

        file_metadata = await self.file_storage.save_file(
            file_content=file.file,
            filename=file.filename,
            content_type=file.content_type,
            project_id=int(project_id),
            metadata={"description": description or "", "uploaded_by": str(user_id)},
        )

        document = Document(
            project_id=project_id,
            filename=name or file_metadata.filename,
            content_type=file_metadata.content_type,
            size_bytes=file_metadata.size_bytes,
            storage_path=file_metadata.storage_path,
            metadata=file_metadata.metadata,
        )
        return self.documents_repo.add(document)

    def download_document(self, document_id: UUID, user_id: UUID) -> Document:
        """Download a document if user has access to the project."""
        document = self.documents_repo.get(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")

        membership = self.memberships_repo.get(document.project_id, user_id)
        if not membership:
            raise InsufficientPermissionsError("You don't have access to this project")

        return document

    def update_document(
        self,
        document_id: UUID,
        user_id: UUID,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Update document metadata if user has editor/owner permissions."""
        document = self.documents_repo.get(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")

        membership = self.memberships_repo.get(document.project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can update documents"
            )

        if filename is not None:
            document.filename = filename
        if metadata is not None:
            document.metadata = metadata

        updated_document = self.documents_repo.update(document)
        if not updated_document:
            raise DocumentNotFoundError(
                f"Failed to update document with id {document_id}"
            )

        return updated_document

    async def delete_document(self, document_id: UUID, user_id: UUID) -> None:
        """Delete a document if user has editor/owner permissions."""
        document = self.documents_repo.get(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")

        membership = self.memberships_repo.get(document.project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can delete documents"
            )

        await self.file_storage.delete_file(document.storage_path)
        self.documents_repo.delete(document_id)

    def list_project_documents(self, project_id: UUID, user_id: UUID) -> List[Document]:
        """List all documents in a project if user has access."""
        membership = self.memberships_repo.get(project_id, user_id)
        if not membership:
            raise InsufficientPermissionsError("You don't have access to this project")

        return self.documents_repo.list_by_project(project_id)

    def get_document(self, document_id: UUID, user_id: UUID) -> Document:
        """Get document details if user has access."""
        return self.download_document(document_id, user_id)

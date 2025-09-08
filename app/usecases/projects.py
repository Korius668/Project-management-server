from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.models import Project, ProjectMembership, ProjectRole, Document
from app.domain.exceptions import (
    ProjectNotFoundError,
    UserNotFoundError,
    PermissionDeniedError,
    UserAlreadyMemberError,
    DocumentNotFoundError,
    InsufficientPermissionsError,
)
from app.config import secrets
from app.ports.repositories import (
    ProjectsRepository,
    UsersRepository,
    ProjectMembershipsRepository,
    DocumentsRepository,
)
from app.ports.file_storage import FileStoragePort  # Added file storage port import
from app.api.schemas.responses import (
    ProjectResponse,
    ProjectInfoResponse,
    ProjectListResponse,
    MembershipResponse,
    DocumentResponse,
    DocumentListResponse,
    UploadDocumentsResponse,
)
from fastapi import UploadFile  # Added UploadFile import


class ProjectsService:
    def __init__(
        self,
        projects_repo: ProjectsRepository,
        users_repo: UsersRepository,
        memberships_repo: ProjectMembershipsRepository,
        documents_repo: DocumentsRepository,
        file_storage: FileStoragePort,
    ):  # Added file storage dependency
        self.projects_repo = projects_repo
        self.users_repo = users_repo
        self.memberships_repo = memberships_repo
        self.documents_repo = documents_repo
        self.file_storage = file_storage  # Added file storage

    def create_project(
        self, name: str, description: str, owner_id: UUID
    ) -> ProjectResponse:
        """Tworzy nowy projekt z użytkownikiem jako właścicielem."""
        owner = self.users_repo.get(owner_id)
        if not owner:
            raise UserNotFoundError(f"User with id {owner_id} not found")

        project = Project(name=name, description=description, owner_id=owner_id)
        created_project = self.projects_repo.add(project)

        membership = ProjectMembership(
            project_id=created_project.id, user_id=owner_id, role=ProjectRole.owner
        )
        self.memberships_repo.add(membership)

        return ProjectResponse.from_domain(created_project)

    def get_project(self, project_id: UUID, user_id: UUID) -> ProjectResponse:
        """Pobiera projekt jeśli użytkownik ma do niego dostęp."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if not membership:
            raise PermissionDeniedError("You don't have access to this project")

        return ProjectResponse.from_domain(project)

    def get_user_projects(self, user_id: UUID) -> ProjectListResponse:
        """Pobiera wszystkie projekty użytkownika."""
        user = self.users_repo.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        memberships = self.memberships_repo.list_by_user(user_id)
        projects = []
        for membership in memberships:
            project = self.projects_repo.get(membership.project_id)
            if project:
                projects.append(ProjectResponse.from_domain(project))

        return ProjectListResponse(projects=projects)

    def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ProjectResponse:
        """Aktualizuje projekt jeśli użytkownik ma uprawnienia."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "You don't have permission to edit this project"
            )

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        updated_project = self.projects_repo.update(project)
        return ProjectResponse.from_domain(updated_project)

    def delete_project(self, project_id: UUID, user_id: UUID) -> None:
        """Usuwa projekt jeśli użytkownik jest właścicielem."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if not membership or membership.role != ProjectRole.owner:
            raise InsufficientPermissionsError(
                "Only project owner can delete the project"
            )

        self.projects_repo.delete(project_id)

    def invite_user_to_project(
        self,
        project_id: UUID,
        inviter_id: UUID,
        invited_user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMembership:
        """Zaprasza użytkownika do projektu."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        inviter_membership = self.memberships_repo.get(project_id, inviter_id)
        if not inviter_membership or inviter_membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "You don't have permission to invite users"
            )

        invited_user = self.users_repo.get(invited_user_id)
        if not invited_user:
            raise UserNotFoundError(f"User with id {invited_user_id} not found")

        existing_membership = self.memberships_repo.get(project_id, invited_user_id)
        if existing_membership:
            raise UserAlreadyMemberError("User is already a member of this project")

        membership = ProjectMembership(
            project_id=project_id, user_id=invited_user_id, role=role
        )
        return self.memberships_repo.add(membership)

    def update_user_role(
        self,
        project_id: UUID,
        updater_id: UUID,
        target_user_id: UUID,
        new_role: ProjectRole,
    ) -> ProjectMembership:
        """Aktualizuje rolę użytkownika w projekcie."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        updater_membership = self.memberships_repo.get(project_id, updater_id)
        if not updater_membership or updater_membership.role != ProjectRole.owner:
            raise InsufficientPermissionsError(
                "Only project owner can update user roles"
            )

        target_membership = self.memberships_repo.get(project_id, target_user_id)
        if not target_membership:
            raise UserNotFoundError("User is not a member of this project")

        if target_membership.role == ProjectRole.owner:
            raise InsufficientPermissionsError("Cannot change owner role")

        target_membership.role = new_role
        return self.memberships_repo.update(target_membership)

    def remove_user_from_project(
        self, project_id: UUID, remover_id: UUID, target_user_id: UUID
    ) -> bool:
        """Usuwa użytkownika z projektu."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        remover_membership = self.memberships_repo.get(project_id, remover_id)
        if not remover_membership or remover_membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "You don't have permission to remove users"
            )

        target_membership = self.memberships_repo.get(project_id, target_user_id)
        if not target_membership:
            raise UserNotFoundError("User is not a member of this project")

        if target_membership.role == ProjectRole.owner:
            raise InsufficientPermissionsError("Cannot remove project owner")

        return self.memberships_repo.delete(project_id, target_user_id)

    def get_project_info(self, project_id: UUID, user_id: UUID) -> ProjectInfoResponse:
        """Pobiera pełne informacje o projekcie z członkami i dokumentami."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if not membership:
            raise PermissionDeniedError("You don't have access to this project")

        # Get project members with roles
        memberships = self.memberships_repo.list_by_project(project_id)
        members = []
        for membership in memberships:
            user = self.users_repo.get(membership.user_id)
            if user:
                members.append(
                    MembershipResponse.from_membership_and_user(membership, user)
                )

        # Get project documents
        documents = self.documents_repo.list_by_project(project_id)
        document_responses = [DocumentResponse.from_domain(doc) for doc in documents]

        return ProjectInfoResponse(
            project=ProjectResponse.from_domain(project),
            members=members,
            documents=document_responses,
        )

    def get_project_documents(
        self, project_id: UUID, user_id: UUID
    ) -> DocumentListResponse:
        """Pobiera dokumenty projektu."""
        project = self.projects_repo.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = self.memberships_repo.get(project_id, user_id)
        if not membership:
            raise PermissionDeniedError("You don't have access to this project")

        documents = self.documents_repo.list_by_project(project_id)
        return DocumentListResponse(
            documents=[DocumentResponse.from_domain(doc) for doc in documents]
        )

    async def upload_project_document(
        self,
        project_id: UUID,
        user_id: UUID,
        filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentResponse:
        """Upload a new document to a project."""
        membership = self.memberships_repo.get(project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can upload documents"
            )

        if size_bytes > secrets.max_file_size_mb * 1024 * 1024:
            raise ValueError("File size exceeds maximum limit of 50MB")

        document = Document(
            project_id=project_id,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
            metadata=metadata or {},
        )
        created_document = self.documents_repo.add(document)
        return DocumentResponse.from_domain(created_document)

    async def upload_project_documents(
        self,
        project_id: UUID,
        user_id: UUID,
        files: List[UploadFile],
        metadata: Optional[str] = None,
    ) -> UploadDocumentsResponse:
        """Upload multiple documents to a project using file storage port."""
        membership = self.memberships_repo.get(project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can upload documents"
            )

        uploaded_documents = []

        for file in files:
            file_metadata = await self.file_storage.save_file(
                file_content=file.file,
                filename=file.filename,
                content_type=file.content_type,
                project_id=project_id,
                metadata={"uploaded_by": user_id},
            )

            document = Document(
                project_id=project_id,
                filename=file_metadata.filename,
                content_type=file_metadata.content_type,
                size_bytes=file_metadata.size_bytes,
                storage_path=file_metadata.storage_path,
                metadata=file_metadata.metadata,
            )
            created_document = self.documents_repo.add(document)
            uploaded_documents.append(DocumentResponse.from_domain(created_document))

        return UploadDocumentsResponse(documents=uploaded_documents)

    def get_project_document(
        self, document_id: UUID, user_id: UUID
    ) -> DocumentResponse:
        """Get document details if user has access."""
        document = self.documents_repo.get(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")

        membership = self.memberships_repo.get(document.project_id, user_id)
        if not membership:
            raise PermissionDeniedError("You don't have access to this project")

        return DocumentResponse.from_domain(document)

    async def update_project_document(
        self,
        document_id: UUID,
        user_id: UUID,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentResponse:
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

        return DocumentResponse.from_domain(updated_document)

    async def delete_project_document(self, document_id: UUID, user_id: UUID) -> None:
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

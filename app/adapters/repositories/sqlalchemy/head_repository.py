from uuid import UUID
from typing import Optional, Dict, Any
from io import BytesIO
from fastapi import UploadFile

from app.domain.exceptions import (
    DocumentNotFoundError,
    InsufficientPermissionsError,
    UserNotFoundError,
    PermissionDeniedError,
    ProjectNotFoundError,
    UserAlreadyMemberError,
)
from app.adapters.repositories.sqlalchemy.repositories import (
    SqlAlchemyUsersRepository,
    SqlAlchemyDocumentsRepository,
    SqlAlchemyProjectMembershipsRepository,
    SqlAlchemyProjectsRepository,
)
from app.adapters.repositories.file_storage.local_storage import LocalFileStorageAdapter
from app.ports.head_repository import Repository
from app.domain.models import User, Project, Document, ProjectMembership, ProjectRole


class SqlAlchemyRepository(Repository):
    """The One to rule them all with SqlAlchemy"""

    def __init__(self, session):
        self.session = session

    def create_user(self, login, password_hashed, email) -> User:
        usersRepository = SqlAlchemyUsersRepository(self.session)

        user = User(name=login, email=email, password_hash=password_hashed)
        usersRepository.add(user)
        return user

    def get_user(self, login) -> User:
        usersRepository = SqlAlchemyUsersRepository(self.session)

        return usersRepository.get_by_name(login)

    async def upload_document(
        self,
        project_id: UUID,
        user_id: UUID,
        file: UploadFile,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Document:
        """Upload a new document to a project."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        documentsRepository = SqlAlchemyDocumentsRepository(self.session)
        file_storage = LocalFileStorageAdapter()

        membership = membershipsRepository.get(project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can upload documents"
            )

        file_metadata = await file_storage.save_file(
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
            metadata_=file_metadata.metadata,
        )
        return documentsRepository.add(document)

    async def download_document(
        self, document_id: UUID, user_id: UUID
    ) -> tuple[BytesIO, Document]:
        """Download a document if user has access to the project."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        documentsRepository = SqlAlchemyDocumentsRepository(self.session)
        file_storage = LocalFileStorageAdapter()

        document = documentsRepository.get(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")

        membership = membershipsRepository.get(document.project_id, user_id)
        if not membership:
            raise InsufficientPermissionsError("You don't have access to this project")
        binaryFile = await file_storage.get_file(document.storage_path)

        return binaryFile, document

    def update_document(
        self,
        document_id: UUID,
        user_id: UUID,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """Update document metadata if user has editor/owner permissions."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        documentsRepository = SqlAlchemyDocumentsRepository(self.session)

        document = documentsRepository.get(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")

        membership = membershipsRepository.get(document.project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can update documents"
            )

        if filename is not None:
            document.filename = filename
        if metadata is not None:
            document.metadata_ = metadata

        updated_document = documentsRepository.update(document)
        if not updated_document:
            raise DocumentNotFoundError(
                f"Failed to update document with id {document_id}"
            )
        return updated_document

    async def delete_document(self, document_id: UUID, user_id: UUID) -> None:
        """Delete a document if user has editor/owner permissions."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        documentsRepository = SqlAlchemyDocumentsRepository(self.session)
        file_storage = LocalFileStorageAdapter()

        document = documentsRepository.get(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with id {document_id} not found")

        membership = membershipsRepository.get(document.project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can delete documents"
            )
        await file_storage.delete_file(document.storage_path)
        documentsRepository.delete(document_id)

    def create_project(self, name: str, description: str, owner_id: UUID) -> Project:
        """Create new project with user as owner."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)

        project = Project(name=name, description=description, owner_id=owner_id)
        created_project = projectsRepository.add(project)

        membership = ProjectMembership(
            project_id=created_project.id, user_id=owner_id, role=ProjectRole.owner
        )
        membershipsRepository.add(membership)

        return created_project

    def get_project(self, project_id: UUID, user_id: UUID) -> Project:
        """Get project if user has access."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = membershipsRepository.get(project_id, user_id)
        if not membership:
            raise PermissionDeniedError("You don't have access to this project")

        return project

    def get_user_projects(self, user_id: UUID) -> list[Project]:
        """Get all user projects."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)
        usersRepository = SqlAlchemyUsersRepository(self.session)

        user = usersRepository.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        memberships = membershipsRepository.list_by_user(user_id)
        projects = []
        for membership in memberships:
            project = projectsRepository.get(membership.project_id)
            if project:
                projects.append(project)

        return projects

    def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """Aktualizuje projekt jeśli użytkownik ma uprawnienia."""
        session = self.session
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(session)
        projectsRepository = SqlAlchemyProjectsRepository(session)

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = membershipsRepository.get(project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "You don't have permission to edit this project"
            )
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description

        return projectsRepository.update(project)

    def delete_project(
        self,
        project_id: UUID,
        user_id: UUID,
        membershipsRepository=None,
        projectsRepository=None,
    ) -> None:
        """Usuwa projekt jeśli użytkownik jest właścicielem."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = membershipsRepository.get(project_id, user_id)
        if not membership or membership.role != ProjectRole.owner:
            raise InsufficientPermissionsError(
                "Only project owner can delete the project"
            )
        membershipsRepository.delete_by_project(project_id)
        return projectsRepository.delete(project_id)

    def invite_user_to_project(
        self,
        project_id: UUID,
        inviter_id: UUID,
        invited_user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMembership:
        """Zaprasza użytkownika do projektu."""
        usersRepository = SqlAlchemyUsersRepository(self.session)
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        inviter_membership = membershipsRepository.get(project_id, inviter_id)
        if not inviter_membership or inviter_membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "You don't have permission to invite users"
            )

        invited_user = usersRepository.get(invited_user_id)
        if not invited_user:
            raise UserNotFoundError(f"User with id {invited_user_id} not found")

        existing_membership = membershipsRepository.get(project_id, invited_user_id)
        if existing_membership:
            raise UserAlreadyMemberError("User is already a member of this project")

        membership = ProjectMembership(
            project_id=project_id, user_id=invited_user_id, role=role
        )
        return membershipsRepository.add(membership)

    def update_user_role(
        self,
        project_id: UUID,
        updater_id: UUID,
        target_user_id: UUID,
        new_role: ProjectRole,
    ) -> ProjectMembership:
        """Aktualizuje rolę użytkownika w projekcie."""
        usersRepository = SqlAlchemyUsersRepository(self.session)
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)

        target = usersRepository.get(target_user_id)
        if not target:
            raise UserNotFoundError(f"User not found")

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        updater_membership = membershipsRepository.get(project_id, updater_id)
        if not updater_membership or updater_membership.role != ProjectRole.owner:
            raise InsufficientPermissionsError(
                "Only project owner can update user roles"
            )
        target_membership = membershipsRepository.get(project_id, target_user_id)
        if not target_membership:
            raise UserNotFoundError("User is not a member of this project")

        if target_membership.role == ProjectRole.owner:
            raise InsufficientPermissionsError("Cannot change owner role")

        target_membership.role = new_role
        return membershipsRepository.update(target_membership)

    def remove_user_from_project(
        self, project_id: UUID, remover_id: UUID, target_user_id: UUID
    ) -> bool:
        """Usuwa użytkownika z projektu."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        remover_membership = membershipsRepository.get(project_id, remover_id)
        if not remover_membership or remover_membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "You don't have permission to remove users"
            )

        target_membership = membershipsRepository.get(project_id, target_user_id)
        if not target_membership:
            raise UserNotFoundError("User is not a member of this project")

        if target_membership.role == ProjectRole.owner:
            raise InsufficientPermissionsError("Cannot remove project owner")

        return membershipsRepository.delete(project_id, target_user_id)

    def get_project_info(self, project_id: UUID, user_id: UUID) -> dict:
        """Pobiera pełne informacje o projekcie z członkami i dokumentami."""
        usersRepository = SqlAlchemyUsersRepository(self.session)
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)
        documentsRepository = SqlAlchemyDocumentsRepository(self.session)

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = membershipsRepository.get(project_id, user_id)
        if not membership:
            raise PermissionDeniedError("You don't have access to this project")

        memberships = membershipsRepository.list_by_project(project_id)
        members = []
        for membership in memberships:
            user = usersRepository.get(membership.user_id)
            if user:
                members.append([membership.role, user])
        documents = documentsRepository.list_by_project(project_id)

        return {"project": project, "members": members, "documents": documents}

    def get_project_documents(self, project_id: UUID, user_id: UUID) -> list[Document]:
        """Pobiera dokumenty projektu."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)
        projectsRepository = SqlAlchemyProjectsRepository(self.session)
        documentsRepository = SqlAlchemyDocumentsRepository(self.session)

        project = projectsRepository.get(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with id {project_id} not found")

        membership = membershipsRepository.get(project_id, user_id)
        if not membership:
            raise PermissionDeniedError("You don't have access to this project")

        return documentsRepository.list_by_project(project_id)

    async def upload_project_documents(
        self, project_id: UUID, user_id: UUID, files: list[UploadFile]
    ) -> list[Document]:
        """Upload multiple documents to a project using file storage port."""
        membershipsRepository = SqlAlchemyProjectMembershipsRepository(self.session)

        membership = membershipsRepository.get(project_id, user_id)
        if not membership or membership.role == ProjectRole.viewer:
            raise InsufficientPermissionsError(
                "Only editors and owners can upload documents"
            )
        uploaded_documents = []

        for file in files:
            document = await self.upload_document(project_id, user_id, file)
            if document is not None:
                uploaded_documents.append(document)

        return uploaded_documents

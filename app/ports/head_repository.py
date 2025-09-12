from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any, BinaryIO
from uuid import UUID
from fastapi import UploadFile

from app.domain.models import Project, ProjectMembership, ProjectRole, Document, User


class Repository(ABC):
    """one to rule them all"""

    @abstractmethod
    def __init__(self, session):
        pass

    @abstractmethod
    def get_user(self, username) -> User:
        pass

    @abstractmethod
    def create_user(self, login, password_hashed, email):
        pass

    @abstractmethod
    async def upload_document(
        self,
        project_id: UUID,
        user_id: UUID,
        file: UploadFile,
        name: Optional[str],
        description: Optional[str],
    ) -> Document:
        """Upload a new document to a project."""

    @abstractmethod
    async def download_document(self, document_id: UUID, user_id: UUID) -> BinaryIO:
        """Download a document if user has access to the project."""

    @abstractmethod
    def update_document(
        self,
        document_id: UUID,
        user_id: UUID,
        filename: Optional[str],
        metadata: Optional[Dict[str, Any]],
    ) -> Document:
        """Update document metadata if user has editor/owner permissions."""

    @abstractmethod
    async def delete_document(self, document_id: UUID, user_id: UUID) -> None:
        """Delete a document if user has editor/owner permissions."""

    @abstractmethod
    def create_project(self, name: str, description: str, owner_id: UUID) -> Project:
        """Create new project with user as owner."""

    @abstractmethod
    def get_project(self, project_id: UUID, user_id: UUID) -> Project:
        """Get project if user has access."""

    @abstractmethod
    def get_user_projects(self, user_id: UUID) -> list[Project]:
        """Get all user projects."""

    @abstractmethod
    def update_project(
        self,
        project_id: UUID,
        user_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """Aktualizuje projekt jeśli użytkownik ma uprawnienia."""

    @abstractmethod
    def delete_project(
        self,
        project_id: UUID,
        user_id: UUID,
        membershipsRepository=None,
        projectsRepository=None,
    ) -> None:
        """Usuwa projekt jeśli użytkownik jest właścicielem."""

    @abstractmethod
    def invite_user_to_project(
        self,
        project_id: UUID,
        inviter_id: UUID,
        invited_user_id: UUID,
        role: ProjectRole,
    ) -> ProjectMembership:
        """Zaprasza użytkownika do projektu."""

    @abstractmethod
    def update_user_role(
        self,
        project_id: UUID,
        updater_id: UUID,
        target_user_id: UUID,
        new_role: ProjectRole,
    ) -> ProjectMembership:
        """Aktualizuje rolę użytkownika w projekcie."""

    @abstractmethod
    def remove_user_from_project(
        self, project_id: UUID, remover_id: UUID, target_user_id: UUID
    ) -> bool:
        """Usuwa użytkownika z projektu."""

    @abstractmethod
    def get_project_info(self, project_id: UUID, user_id: UUID) -> dict:
        """Pobiera pełne informacje o projekcie z członkami i dokumentami."""

    @abstractmethod
    def get_project_documents(self, project_id: UUID, user_id: UUID) -> list[Document]:
        """Pobiera dokumenty projektu."""

    @abstractmethod
    async def upload_project_documents(
        self, project_id: UUID, user_id: UUID, files: list[UploadFile]
    ) -> list[Document]:
        """Upload multiple documents to a project using file storage port."""

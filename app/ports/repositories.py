from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models import Project, User, Document, ProjectMembership, ProjectRole


class UsersRepository(ABC):

    @abstractmethod
    def add(self, user: User) -> User:
        """Add a new user"""

    @abstractmethod
    def get(self, user_id: UUID) -> User:
        """Retrieve a user by id"""

    @abstractmethod
    def list(self) -> List[User]:
        """Return all users"""

    @abstractmethod
    def delete(self, user_id: UUID) -> None:
        """Delete a user by id"""


class ProjectsRepository(ABC):

    @abstractmethod
    def add(self, project: Project) -> Project:
        """Add a new project"""

    @abstractmethod
    def update(self, project: Project) -> Project:
        """Update project info"""

    @abstractmethod
    def get(self, project_id: UUID) -> Project:
        """Retrieve a project by id"""

    @abstractmethod
    def list(self) -> List[Project]:
        """Return all projects"""

    @abstractmethod
    def delete(self, project_id: UUID) -> None:
        """Delete a project by id"""


class DocumentsRepository(ABC):

    @abstractmethod
    def add(self, document: Document) -> Document:
        """Add a new document"""

    @abstractmethod
    def get(self, task_id: UUID) -> Document:
        """Retrieve a document by id"""

    @abstractmethod
    def update(self, document: Document) -> Document:
        """Update document info"""

    @abstractmethod
    def list(self) -> List[Document]:
        """Return all documents"""

    @abstractmethod
    def list_by_project(self, project_id) -> List[Document]:
        """Return all documents with project id"""

    @abstractmethod
    def delete(self, document_id: UUID) -> None:
        """Delete a document by id"""


class ProjectMembershipsRepository(ABC):

    @abstractmethod
    def add(self, project_membership: ProjectMembership) -> ProjectMembership:
        """Add a new membership"""

    @abstractmethod
    def get(self, project_id: UUID, user_id: UUID) -> ProjectMembership:
        """Get a membership"""

    @abstractmethod
    def update(self, project_membership: ProjectMembership) -> ProjectMembership:
        """Update a membership"""

    @abstractmethod
    def list(self):
        """Return all memberships"""

    @abstractmethod
    def list_by_project(self, project_id) -> List[ProjectMembership]:
        """Return memberships with project id"""

    @abstractmethod
    def list_by_user(self, user_id) -> List[ProjectMembership]:
        """Return documents with user id"""

    @abstractmethod
    def delete(self, project_membership: ProjectMembership) -> None:
        """Delete a membership"""

    @abstractmethod
    def delete_by_project(self, project_id: UUID) -> None:
        """Delete memberships of project"""

    @abstractmethod
    def delete_by_user(self, user_id: UUID) -> None:
        """Delete memberships of user"""

    @abstractmethod
    def exists(self, project_id: UUID, user_id: UUID) -> bool:
        """Check if membership exists"""

    @abstractmethod
    def count_by_project(self, project_id: UUID) -> int:
        """Count members in a project"""

    @abstractmethod
    def get_user_role(self, project_id: UUID, user_id: UUID) -> Optional[ProjectRole]:
        """Get user's role in a project"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.models import Project, User, Document, ProjectMembership


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
    def list_with_project_id(self, project_id) -> List[Document]:
        """Return all documents with project id"""

    @abstractmethod
    def delete(self, document_id: UUID) -> None:
        """Delete a document by id""" 

class ProjectMembershipsRepository(ABC):

    @abstractmethod
    def add(self, project_membership: ProjectMembership) -> ProjectMembership:
        """Add a new membership"""
    
    @abstractmethod
    def list_with_project_id(self, project_id) -> List[ProjectMembership]:
        """Return all memberships with project id"""
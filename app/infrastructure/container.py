from functools import lru_cache
from sqlalchemy.orm import Session

from app.adapters.sqlalchemy.repositories import (
    SqlAlchemyUsersRepository,
    SqlAlchemyProjectsRepository,
    SqlAlchemyDocumentsRepository,
    SqlAlchemyProjectMembershipsRepository,
)
from app.usecases.auth import UsersService
from app.usecases.projects import ProjectsService
from app.usecases.documents import DocumentsService  # Added DocumentsService import
from app.ports.repositories import (
    UsersRepository,
    ProjectsRepository,
    DocumentsRepository,
    ProjectMembershipsRepository,
)
from app.ports.file_storage import FileStoragePort
from app.adapters.file_storage.local_storage import LocalFileStorageAdapter


class DependencyContainer:
    """Dependency Injection Container zgodny z hexagonalną architekturą."""

    def __init__(self, session: Session):
        self.session = session
        self._users_repo = None
        self._projects_repo = None
        self._documents_repo = None
        self._memberships_repo = None
        self._file_storage = None

    @property
    def users_repository(self) -> UsersRepository:
        """Lazy loading users repository."""
        if self._users_repo is None:
            self._users_repo = SqlAlchemyUsersRepository(self.session)
        return self._users_repo

    @property
    def projects_repository(self) -> ProjectsRepository:
        """Lazy loading projects repository."""
        if self._projects_repo is None:
            self._projects_repo = SqlAlchemyProjectsRepository(self.session)
        return self._projects_repo

    @property
    def documents_repository(self) -> DocumentsRepository:
        """Lazy loading documents repository."""
        if self._documents_repo is None:
            self._documents_repo = SqlAlchemyDocumentsRepository(self.session)
        return self._documents_repo

    @property
    def memberships_repository(self) -> ProjectMembershipsRepository:
        """Lazy loading memberships repository."""
        if self._memberships_repo is None:
            self._memberships_repo = SqlAlchemyProjectMembershipsRepository(
                self.session
            )
        return self._memberships_repo

    @property
    def file_storage(self) -> FileStoragePort:
        """Lazy loading file storage."""
        if self._file_storage is None:
            self._file_storage = LocalFileStorageAdapter()
        return self._file_storage

    def users_service(self) -> UsersService:
        """Tworzy UsersService z wstrzykniętymi zależnościami."""
        return UsersService(self.users_repository)

    def projects_service(self) -> ProjectsService:
        """Tworzy ProjectsService z wstrzykniętymi zależnościami."""
        return ProjectsService(
            projects_repo=self.projects_repository,
            users_repo=self.users_repository,
            memberships_repo=self.memberships_repository,
            documents_repo=self.documents_repository,  # Added documents repository
            file_storage=self.file_storage,  # Added file storage dependency
        )

    def documents_service(self) -> DocumentsService:
        """Tworzy DocumentsService z wstrzykniętymi zależnościami."""
        return DocumentsService(
            documents_repo=self.documents_repository,
            memberships_repo=self.memberships_repository,
            file_storage=self.file_storage,
        )


@lru_cache()
def get_container(session: Session) -> DependencyContainer:
    """Factory function dla dependency container."""
    return DependencyContainer(session)

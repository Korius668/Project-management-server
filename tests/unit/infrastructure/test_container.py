import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.infrastructure.container import DependencyContainer, get_container
from app.usecases.auth import UsersService
from app.usecases.projects import ProjectsService


class TestDependencyContainer:
    def test_users_repository_lazy_loading(self, mock_session):
        # Given
        container = DependencyContainer(mock_session)
        
        # When
        repo1 = container.users_repository
        repo2 = container.users_repository
        
        # Then
        assert repo1 is repo2  # Same instance (lazy loading)

    def test_projects_repository_lazy_loading(self, mock_session):
        # Given
        container = DependencyContainer(mock_session)
        
        # When
        repo1 = container.projects_repository
        repo2 = container.projects_repository
        
        # Then
        assert repo1 is repo2  # Same instance (lazy loading)

    def test_memberships_repository_lazy_loading(self, mock_session):
        # Given
        container = DependencyContainer(mock_session)
        
        # When
        repo1 = container.memberships_repository
        repo2 = container.memberships_repository
        
        # Then
        assert repo1 is repo2  # Same instance (lazy loading)

    def test_documents_repository_lazy_loading(self, mock_session):
        # Given
        container = DependencyContainer(mock_session)
        
        # When
        repo1 = container.documents_repository
        repo2 = container.documents_repository
        
        # Then
        assert repo1 is repo2  # Same instance (lazy loading)

    def test_users_service_creation(self, mock_session):
        # Given
        container = DependencyContainer(mock_session)
        
        # When
        service = container.users_service()
        
        # Then
        assert isinstance(service, UsersService)

    def test_projects_service_creation(self, mock_session):
        # Given
        container = DependencyContainer(mock_session)
        
        # When
        service = container.projects_service()
        
        # Then
        assert isinstance(service, ProjectsService)

    def test_get_container_caching(self, mock_session):
        # When
        container1 = get_container(mock_session)
        container2 = get_container(mock_session)
        
        # Then
        assert container1 is container2  # Cached by lru_cache

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from app.adapters.sqlalchemy.repositories import (
    SqlAlchemyUsersRepository,
    SqlAlchemyProjectsRepository,
    SqlAlchemyDocumentsRepository,
    SqlAlchemyProjectMembershipsRepository
)
from app.adapters.sqlalchemy.models import UserORM, ProjectORM, DocumentORM, ProjectMembershipORM
from app.domain.models import User, Project, Document, ProjectMembership, ProjectRole


class TestSqlAlchemyUsersRepository:
    
    def test_add_user_success(self, sample_user):
        # Given
        mock_session = Mock()
        repo = SqlAlchemyUsersRepository(mock_session)
        
        user = sample_user
        
        # When
        result = repo.add(user)
        
        # Then
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result == user
        
        # Verify ORM object was created correctly
        orm_call = mock_session.add.call_args[0][0]
        assert isinstance(orm_call, UserORM)
        assert orm_call.id == user.id
        assert orm_call.email == user.email
        assert orm_call.name == user.name
        assert orm_call.password_hash == user.password_hash

    def test_get_user_found(self):
        # Given
        mock_session = Mock()
        user_id = uuid4()
        
        # Mock ORM object
        mock_orm = Mock(spec=UserORM)
        mock_orm.id = user_id
        mock_orm.email = "test@example.com"
        mock_orm.name = "Test User"
        mock_orm.password_hash = "hashed"
        
        mock_session.get.return_value = mock_orm
        repo = SqlAlchemyUsersRepository(mock_session)
        
        # When
        result = repo.get(user_id)
        
        # Then
        mock_session.get.assert_called_once_with(UserORM, user_id)
        assert result is not None
        assert result.id == user_id
        assert result.email == "test@example.com"
        assert result.name == "Test User"

    def test_get_user_not_found(self):
        # Given
        mock_session = Mock()
        mock_session.get.return_value = None
        repo = SqlAlchemyUsersRepository(mock_session)
        user_id = uuid4()
        
        # When
        result = repo.get(user_id)
        
        # Then
        mock_session.get.assert_called_once_with(UserORM, user_id)
        assert result is None

    def test_list_users(self):
        # Given
        mock_session = Mock()
        
        # Mock ORM objects
        mock_orms = []
        for i in range(3):
            mock_orm = Mock(spec=UserORM)
            mock_orm.id = uuid4()
            mock_orm.email = f"user{i}@example.com"
            mock_orm.name = f"User {i}"
            mock_orm.password_hash = "hashed"
            mock_orms.append(mock_orm)
        
        mock_query = Mock()
        mock_query.all.return_value = mock_orms
        mock_session.query.return_value = mock_query
        
        repo = SqlAlchemyUsersRepository(mock_session)
        
        # When
        result = repo.list()
        
        # Then
        mock_session.query.assert_called_once_with(UserORM)
        mock_query.all.assert_called_once()
        assert len(result) == 3
        assert all(isinstance(user, User) for user in result)
        assert result[0].email == "user0@example.com"
        assert result[1].email == "user1@example.com"
        assert result[2].email == "user2@example.com"


class TestSqlAlchemyProjectsRepository:
    
    def test_update_project_success(self, sample_project):
        # Given
        mock_session = Mock()
        
        # Mock existing ORM object
        mock_orm = Mock(spec=ProjectORM)
        mock_session.get.return_value = mock_orm
        
        repo = SqlAlchemyProjectsRepository(mock_session)
        
        updated_project = sample_project
        
        # When
        result = repo.update(updated_project)
        
        # Then
        mock_session.get.assert_called_once_with(ProjectORM, updated_project.id)
        assert mock_orm.name == updated_project.name
        assert mock_orm.description == updated_project.description
        mock_session.commit.assert_called_once()
        assert result == updated_project

    def test_update_project_not_found(self, sample_project):
        # Given
        mock_session = Mock()
        mock_session.get.return_value = None
        repo = SqlAlchemyProjectsRepository(mock_session)
        
        project = sample_project
        
        # When
        result = repo.update(project)
        
        # Then
        mock_session.get.assert_called_once_with(ProjectORM, project.id)
        mock_session.commit.assert_not_called()
        assert result is None

    def test_get_project_found(self):
        # Given
        mock_session = Mock()
        project_id = uuid4()
        owner_id = uuid4()
        
        # Mock ORM object
        mock_orm = Mock(spec=ProjectORM)
        mock_orm.id = project_id
        mock_orm.owner_id = owner_id
        mock_orm.name = "Test Project"
        mock_orm.description = "Test Description"
        
        mock_session.get.return_value = mock_orm
        repo = SqlAlchemyProjectsRepository(mock_session)
        
        # When
        result = repo.get(project_id)
        
        # Then
        mock_session.get.assert_called_once_with(ProjectORM, project_id)
        assert result is not None
        assert result.id == project_id
        assert result.owner_id == owner_id
        assert result.name == "Test Project"
        assert result.description == "Test Description"

    def test_get_project_not_found(self):
        # Given
        mock_session = Mock()
        mock_session.get.return_value = None
        repo = SqlAlchemyProjectsRepository(mock_session)
        project_id = uuid4()
        
        # When
        result = repo.get(project_id)
        
        # Then
        mock_session.get.assert_called_once_with(ProjectORM, project_id)
        assert result is None

    def test_list_projects(self):
        # Given
        mock_session = Mock()
        
        # Mock ORM objects
        mock_orms = []
        for i in range(2):
            mock_orm = Mock(spec=ProjectORM)
            mock_orm.id = uuid4()
            mock_orm.owner_id = uuid4()
            mock_orm.name = f"Project {i}"
            mock_orm.description = f"Description {i}"
            mock_orms.append(mock_orm)
        
        mock_query = Mock()
        mock_query.all.return_value = mock_orms
        mock_session.query.return_value = mock_query
        
        repo = SqlAlchemyProjectsRepository(mock_session)
        
        # When
        result = repo.list()
        
        # Then
        mock_session.query.assert_called_once_with(ProjectORM)
        mock_query.all.assert_called_once()
        assert len(result) == 2
        assert all(isinstance(project, Project) for project in result)
        assert result[0].name == "Project 0"
        assert result[1].name == "Project 1"

    def test_delete_project_exists(self):
        # Given
        mock_session = Mock()
        project_id = uuid4()
        mock_orm = Mock(spec=ProjectORM)
        mock_session.get.return_value = mock_orm
        
        repo = SqlAlchemyProjectsRepository(mock_session)
        
        # When
        repo.delete(project_id)
        
        # Then
        mock_session.get.assert_called_once_with(ProjectORM, project_id)
        mock_session.delete.assert_called_once_with(mock_orm)
        mock_session.commit.assert_called_once()

    def test_delete_project_not_exists(self):
        # Given
        mock_session = Mock()
        project_id = uuid4()
        mock_session.get.return_value = None
        
        repo = SqlAlchemyProjectsRepository(mock_session)
        
        # When
        repo.delete(project_id)
        
        # Then
        mock_session.get.assert_called_once_with(ProjectORM, project_id)
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()


class TestSqlAlchemyDocumentsRepository:

    def test_add_document_success(self, sample_document):
        # Given
        mock_session = Mock()
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        document = sample_document
        
        # When
        result = repo.add(document)
        
        # Then
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result == document
        
        # Verify ORM object
        orm_call = mock_session.add.call_args[0][0]
        assert isinstance(orm_call, DocumentORM)
        assert orm_call.id == document.id
        assert orm_call.project_id == document.project_id
        assert orm_call.filename == document.filename
        assert orm_call.content_type == document.content_type
        assert orm_call.size_bytes == document.size_bytes
        assert orm_call.storage_path == document.storage_path
        assert orm_call.metadata_json == document.metadata

    def test_get_document_found(self):
        # Given
        mock_session = Mock()
        document_id = uuid4()
        project_id = uuid4()
        
        # Mock ORM object
        mock_orm = Mock(spec=DocumentORM)
        mock_orm.id = document_id
        mock_orm.project_id = project_id
        mock_orm.filename = "test.pdf"
        mock_orm.content_type = "application/pdf"
        mock_orm.size_bytes = 1024
        mock_orm.storage_path = "/storage/test.pdf"
        mock_orm.metadata = {"uploader_id": str(uuid4()), "version": 1}
        
        mock_session.get.return_value = mock_orm
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        # When
        result = repo.get(document_id)
        
        # Then
        mock_session.get.assert_called_once_with(DocumentORM, document_id)
        assert result is not None
        assert result.id == document_id
        assert result.project_id == project_id
        assert result.filename == "test.pdf"
        assert result.content_type == "application/pdf"
        assert result.size_bytes == 1024
        assert result.storage_path == "/storage/test.pdf"

    def test_get_document_not_found(self):
        # Given
        mock_session = Mock()
        mock_session.get.return_value = None
        repo = SqlAlchemyDocumentsRepository(mock_session)
        document_id = uuid4()
        
        # When
        result = repo.get(document_id)
        
        # Then
        mock_session.get.assert_called_once_with(DocumentORM, document_id)
        assert result is None

    def test_update_document_success(self, sample_document):
        # Given
        mock_session = Mock()
        
        # Mock existing ORM object
        mock_orm = Mock(spec=DocumentORM)
        mock_session.get.return_value = mock_orm
        
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        updated_document = sample_document
        
        # When
        result = repo.update(updated_document)
        
        # Then
        mock_session.get.assert_called_once_with(DocumentORM, updated_document.id)
        assert mock_orm.filename == updated_document.filename
        assert mock_orm.content_type == updated_document.content_type
        assert mock_orm.size_bytes == updated_document.size_bytes
        assert mock_orm.storage_path == updated_document.storage_path
        assert mock_orm.metadata_json == updated_document.metadata
        mock_session.commit.assert_called_once()
        assert result == updated_document

    def test_update_document_not_found(self, sample_document):
        # Given
        mock_session = Mock()
        mock_session.get.return_value = None
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        document = sample_document
        
        # When
        result = repo.update(document)
        
        # Then
        mock_session.get.assert_called_once_with(DocumentORM, document.id)
        mock_session.commit.assert_not_called()
        assert result is None

    def test_list_documents(self):
        # Given
        mock_session = Mock()
        
        # Mock ORM objects
        mock_orms = []
        for i in range(3):
            mock_orm = Mock(spec=DocumentORM)
            mock_orm.id = uuid4()
            mock_orm.project_id = uuid4()
            mock_orm.filename = f"file{i}.pdf"
            mock_orm.content_type = "application/pdf"
            mock_orm.size_bytes = 1024 * (i + 1)
            mock_orm.storage_path = f"/storage/file{i}.pdf"
            mock_orm.metadata = {"version": i + 1}
            mock_orms.append(mock_orm)
        
        mock_query = Mock()
        mock_query.all.return_value = mock_orms
        mock_session.query.return_value = mock_query
        
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        # When
        result = repo.list()
        
        # Then
        mock_session.query.assert_called_once_with(DocumentORM)
        mock_query.all.assert_called_once()
        assert len(result) == 3
        assert all(isinstance(doc, Document) for doc in result)
        assert result[0].filename == "file0.pdf"
        assert result[1].filename == "file1.pdf"
        assert result[2].filename == "file2.pdf"

    def test_list_with_project_id(self):
        # Given
        mock_session = Mock()
        project_id = uuid4()
        
        # Mock ORM objects
        mock_orms = []
        for i in range(2):
            mock_orm = Mock(spec=DocumentORM)
            mock_orm.id = uuid4()
            mock_orm.project_id = project_id
            mock_orm.filename = f"project_file{i}.pdf"
            mock_orm.content_type = "application/pdf"
            mock_orm.size_bytes = 1024
            mock_orm.storage_path = f"/storage/project_file{i}.pdf"
            mock_orm.metadata = {"project_specific": True}
            mock_orms.append(mock_orm)
        
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = mock_orms
        mock_query.filter_by.return_value = mock_filter
        mock_session.query.return_value = mock_query
        
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        # When
        result = repo.list_with_project_id(project_id)
        
        # Then
        mock_session.query.assert_called_once_with(DocumentORM)
        mock_query.filter_by.assert_called_once_with(project_id=project_id)
        mock_filter.all.assert_called_once()
        assert len(result) == 2
        assert all(isinstance(doc, Document) for doc in result)
        assert all(doc.project_id == project_id for doc in result)

    def test_delete_document_exists(self):
        # Given
        mock_session = Mock()
        document_id = uuid4()
        mock_orm = Mock(spec=DocumentORM)
        mock_session.get.return_value = mock_orm
        
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        # When
        repo.delete(document_id)
        
        # Then
        mock_session.get.assert_called_once_with(DocumentORM, document_id)
        mock_session.delete.assert_called_once_with(mock_orm)
        mock_session.commit.assert_called_once()

    def test_delete_document_not_exists(self):
        # Given
        mock_session = Mock()
        document_id = uuid4()
        mock_session.get.return_value = None
        
        repo = SqlAlchemyDocumentsRepository(mock_session)
        
        # When
        repo.delete(document_id)
        
        # Then
        mock_session.get.assert_called_once_with(DocumentORM, document_id)
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()


class TestSqlAlchemyProjectMembershipsRepository:

    def test_add_membership_success(self, sample_membership):
        # Given
        mock_session = Mock()
        repo = SqlAlchemyProjectMembershipsRepository(mock_session)
        
        membership = sample_membership
        
        # When
        result = repo.add(membership)
        
        # Then
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result == membership
        
        # Verify ORM object
        orm_call = mock_session.add.call_args[0][0]
        assert isinstance(orm_call, ProjectMembershipORM)
        assert orm_call.project_id == membership.project_id
        assert orm_call.user_id == membership.user_id
        assert orm_call.role == membership.role

    def test_list_with_project_id(self):
        # Given
        mock_session = Mock()
        project_id = uuid4()
        
        # Mock ORM objects
        mock_orms = []
        roles = [ProjectRole.owner, ProjectRole.editor, ProjectRole.viewer]
        for i, role in enumerate(roles):
            mock_orm = Mock(spec=ProjectMembershipORM)
            mock_orm.project_id = project_id
            mock_orm.user_id = uuid4()
            mock_orm.role = role.value
            mock_orms.append(mock_orm)
        
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = mock_orms
        mock_query.filter_by.return_value = mock_filter
        mock_session.query.return_value = mock_query
        
        repo = SqlAlchemyProjectMembershipsRepository(mock_session)
        
        # When
        result = repo.list_with_project_id(project_id)
        
        # Then
        mock_session.query.assert_called_once_with(ProjectMembershipORM)
        mock_query.filter_by.assert_called_once_with(project_id=project_id)
        mock_filter.all.assert_called_once()
        assert len(result) == 3
        assert all(isinstance(membership, ProjectMembership) for membership in result)
        assert all(membership.project_id == project_id for membership in result)
        assert result[0].role == ProjectRole.owner
        assert result[1].role == ProjectRole.editor
        assert result[2].role == ProjectRole.viewer
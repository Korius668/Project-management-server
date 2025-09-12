"""Integration tests for repository layer."""

import pytest
import uuid

from app.domain.models import User, Project, Document, ProjectMembership, ProjectRole
from app.domain.exceptions import (
    UserAlreadyExistsError,
    ProjectAlreadyExistsError,
    DocumentAlreadyExistsError,
    UserNotFoundError,
)
from app.adapters.repositories.sqlalchemy.repositories import (
    SqlAlchemyUsersRepository,
    SqlAlchemyProjectsRepository,
    SqlAlchemyDocumentsRepository,
    SqlAlchemyProjectMembershipsRepository,
)


class TestUsersRepository:
    """Test users repository integration."""

    def test_add_user_success(self, test_session):
        """Test successful user creation."""
        repo = SqlAlchemyUsersRepository(test_session)
        user = User(
            name="testuser", email="test@example.com", password_hash="hashed_password"
        )

        result = repo.add(user)

        assert result.id == user.id
        assert result.name == "testuser"
        assert result.email == "test@example.com"

    def test_add_user_duplicate_email_raises_error(self, test_session):
        """Test that duplicate email raises error."""
        session = test_session
        repo = SqlAlchemyUsersRepository(session)
        user1 = User(
            name="user1", email="test@example.com", password_hash="hashed_password"
        )
        user2 = User(
            name="user2",
            email="test@example.com",  # Same email
            password_hash="hashed_password",
        )

        repo.add(user1)

        with pytest.raises(UserAlreadyExistsError):
            repo.add(user2)

    def test_add_user_duplicate_name_raises_error(self, test_session):
        """Test that duplicate name raises error."""
        session = test_session
        repo = SqlAlchemyUsersRepository(session)
        user1 = User(
            name="testuser", email="test1@example.com", password_hash="hashed_password"
        )
        user2 = User(
            name="testuser",  # Same name
            email="test2@example.com",
            password_hash="hashed_password",
        )

        repo.add(user1)

        with pytest.raises(UserAlreadyExistsError):
            repo.add(user2)

    def test_get_user_by_id_success(self, test_session):
        """Test getting user by ID."""
        session = test_session
        repo = SqlAlchemyUsersRepository(session)
        user = User(
            name="testuser", email="test@example.com", password_hash="hashed_password"
        )
        repo.add(user)

        result = repo.get(user.id)

        assert result is not None
        assert result.id == user.id
        assert result.name == "testuser"

    def test_get_user_by_id_not_found(self, test_session):
        """Test getting non-existent user by ID."""
        repo = SqlAlchemyUsersRepository(test_session)

        result = repo.get(uuid.uuid4())

        assert result is None

    def test_get_user_by_name_success(self, test_session):
        """Test getting user by email."""
        session = test_session
        repo = SqlAlchemyUsersRepository(session)
        user = User(
            name="testuser", email="test@example.com", password_hash="hashed_password"
        )
        repo.add(user)

        result = repo.get_by_name("testuser")

        assert result is not None
        assert result.email == "test@example.com"

    def test_list_users(self, test_session):
        """Test listing all users."""
        session = test_session
        repo = SqlAlchemyUsersRepository(session)
        user1 = User(name="user1", email="test1@example.com", password_hash="hash1")
        user2 = User(name="user2", email="test2@example.com", password_hash="hash2")

        repo.add(user1)
        repo.add(user2)

        result = repo.list()

        assert len(result) == 2
        assert any(u.name == "user1" for u in result)
        assert any(u.name == "user2" for u in result)

    def test_delete_user_success(self, test_session):
        """Test successful user deletion."""
        session = test_session
        repo = SqlAlchemyUsersRepository(session)
        user = User(
            name="testuser", email="test@example.com", password_hash="hashed_password"
        )
        repo.add(user)

        repo.delete(user.id)

        result = repo.get(user.id)
        assert result is None

    def test_delete_user_not_found_raises_error(self, test_session):
        """Test deleting non-existent user raises error."""
        session = test_session
        repo = SqlAlchemyUsersRepository(session)

        with pytest.raises(UserNotFoundError):
            repo.delete(uuid.uuid4())


class TestProjectsRepository:
    """Test projects repository integration."""

    def test_add_project_success(self, test_session):
        """Test successful project creation."""
        # First create a user
        users_repo = SqlAlchemyUsersRepository(test_session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        # Then create project
        projects_repo = SqlAlchemyProjectsRepository(test_session)
        project = Project(
            owner_id=user.id, name="Test Project", description="A test project"
        )

        result = projects_repo.add(project)

        assert result.id == project.id
        assert result.name == "Test Project"
        assert result.owner_id == user.id

    def test_add_project_duplicate_name_raises_error(self, test_session):
        """Test that duplicate project name raises error."""
        # Create user
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        # Create projects with same name
        projects_repo = SqlAlchemyProjectsRepository(test_session)
        project1 = Project(owner_id=user.id, name="Test Project", description="First")
        project2 = Project(owner_id=user.id, name="Test Project", description="Second")

        projects_repo.add(project1)

        with pytest.raises(
            ProjectAlreadyExistsError,
            match="Project with name Test Project already exists",
        ):
            projects_repo.add(project2)

    def test_get_project_success(self, test_session):
        """Test getting project by ID."""
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        projects_repo = SqlAlchemyProjectsRepository(test_session)
        project = Project(owner_id=user.id, name="Test Project", description="Test")
        projects_repo.add(project)

        result = projects_repo.get(project.id)

        assert result is not None
        assert result.id == project.id
        assert result.name == "Test Project"

    def test_update_project_success(self, test_session):
        """Test updating project."""
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        projects_repo = SqlAlchemyProjectsRepository(test_session)
        project = Project(
            owner_id=user.id, name="Original Name", description="Original"
        )
        projects_repo.add(project)

        # Update project
        project.name = "Updated Name"
        project.description = "Updated description"

        result = projects_repo.update(project)

        assert result is not None
        assert result.name == "Updated Name"
        assert result.description == "Updated description"

    def test_delete_project_success(self, test_session):
        """Test deleting project."""
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        projects_repo = SqlAlchemyProjectsRepository(test_session)
        project = Project(owner_id=user.id, name="Test Project", description="Test")
        projects_repo.add(project)

        projects_repo.delete(project.id)

        result = projects_repo.get(project.id)
        assert result is None


class TestDocumentsRepository:
    """Test documents repository integration."""

    def test_add_document_success(self, test_session):
        """Test successful document creation."""
        # Create user and project first
        users_repo = SqlAlchemyUsersRepository(test_session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        projects_repo = SqlAlchemyProjectsRepository(test_session)
        project = Project(owner_id=user.id, name="Test Project", description="Test")
        projects_repo.add(project)

        # Create document
        docs_repo = SqlAlchemyDocumentsRepository(test_session)
        document = Document(
            project_id=project.id,
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
            storage_path="project-1/test.txt",
            metadata={"description": "Test file"},
        )

        result = docs_repo.add(document)

        assert result.id == document.id
        assert result.filename == "test.txt"
        assert result.project_id == project.id

    def test_add_document_duplicate_filename_in_project_raises_error(
        self, test_session
    ):
        """Test that duplicate filename in same project raises error."""
        # Create user and project
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        projects_repo = SqlAlchemyProjectsRepository(session)
        project = Project(owner_id=user.id, name="Test Project", description="Test")
        projects_repo.add(project)

        # Create documents with same filename
        docs_repo = SqlAlchemyDocumentsRepository(session)
        doc1 = Document(
            project_id=project.id,
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
            storage_path="project-1/test1.txt",
        )
        doc2 = Document(
            project_id=project.id,
            filename="test.txt",  # Same filename
            content_type="text/plain",
            size_bytes=2048,
            storage_path="project-1/test2.txt",
        )

        docs_repo.add(doc1)

        with pytest.raises(DocumentAlreadyExistsError):
            docs_repo.add(doc2)

    def test_get_document_success(self, test_session):
        """Test getting document by ID."""
        # Create user, project, and document
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        projects_repo = SqlAlchemyProjectsRepository(session)
        project = Project(owner_id=user.id, name="Test Project", description="Test")
        projects_repo.add(project)

        docs_repo = SqlAlchemyDocumentsRepository(session)
        document = Document(
            project_id=project.id,
            filename="test.txt",
            content_type="text/plain",
            size_bytes=1024,
            storage_path="project-1/test.txt",
        )
        docs_repo.add(document)

        result = docs_repo.get(document.id)

        assert result is not None
        assert result.id == document.id
        assert result.filename == "test.txt"

    def test_list_documents_by_project(self, test_session):
        """Test listing documents by project."""
        # Create user and projects
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        user = User(name="owner", email="owner@example.com", password_hash="hash")
        users_repo.add(user)

        projects_repo = SqlAlchemyProjectsRepository(session)
        project1 = Project(owner_id=user.id, name="Project 1", description="Test")
        project2 = Project(owner_id=user.id, name="Project 2", description="Test")
        projects_repo.add(project1)
        projects_repo.add(project2)

        # Create documents
        docs_repo = SqlAlchemyDocumentsRepository(session)
        doc1 = Document(
            project_id=project1.id,
            filename="doc1.txt",
            content_type="text/plain",
            size_bytes=1024,
            storage_path="project-1/doc1.txt",
        )
        doc2 = Document(
            project_id=project1.id,
            filename="doc2.txt",
            content_type="text/plain",
            size_bytes=2048,
            storage_path="project-1/doc2.txt",
        )
        doc3 = Document(
            project_id=project2.id,
            filename="doc3.txt",
            content_type="text/plain",
            size_bytes=1024,
            storage_path="project-2/doc3.txt",
        )

        docs_repo.add(doc1)
        docs_repo.add(doc2)
        docs_repo.add(doc3)

        result = docs_repo.list_by_project(project1.id)

        assert len(result) == 2
        assert any(d.filename == "doc1.txt" for d in result)
        assert any(d.filename == "doc2.txt" for d in result)
        assert not any(d.filename == "doc3.txt" for d in result)


class TestProjectMembershipsRepository:
    """Test project memberships repository integration."""

    def test_add_membership_success(self, test_session):
        """Test successful membership creation."""
        # Create user and project
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        owner = User(name="owner", email="owner@example.com", password_hash="hash")
        member = User(name="member", email="member@example.com", password_hash="hash")
        users_repo.add(owner)
        users_repo.add(member)

        projects_repo = SqlAlchemyProjectsRepository(test_session)
        project = Project(owner_id=owner.id, name="Test Project", description="Test")
        projects_repo.add(project)

        # Create membership
        memberships_repo = SqlAlchemyProjectMembershipsRepository(test_session)
        membership = ProjectMembership(
            project_id=project.id, user_id=member.id, role=ProjectRole.editor
        )

        result = memberships_repo.add(membership)

        assert result.project_id == project.id
        assert result.user_id == member.id
        assert result.role == ProjectRole.editor

    def test_get_membership_success(self, test_session):
        """Test getting membership."""
        # Create user and project
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        owner = User(name="owner", email="owner@example.com", password_hash="hash")
        member = User(name="member", email="member@example.com", password_hash="hash")
        users_repo.add(owner)
        users_repo.add(member)

        projects_repo = SqlAlchemyProjectsRepository(session)
        project = Project(owner_id=owner.id, name="Test Project", description="Test")
        projects_repo.add(project)

        # Create and get membership
        memberships_repo = SqlAlchemyProjectMembershipsRepository(session)
        membership = ProjectMembership(
            project_id=project.id, user_id=member.id, role=ProjectRole.viewer
        )
        memberships_repo.add(membership)

        result = memberships_repo.get(project.id, member.id)

        assert result is not None
        assert result.role == ProjectRole.viewer

    def test_update_membership_role(self, test_session):
        """Test updating membership role."""
        # Create user and project
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        owner = User(name="owner", email="owner@example.com", password_hash="hash")
        member = User(name="member", email="member@example.com", password_hash="hash")
        users_repo.add(owner)
        users_repo.add(member)

        projects_repo = SqlAlchemyProjectsRepository(session)
        project = Project(owner_id=owner.id, name="Test Project", description="Test")
        projects_repo.add(project)

        # Create and update membership
        memberships_repo = SqlAlchemyProjectMembershipsRepository(session)
        membership = ProjectMembership(
            project_id=project.id, user_id=member.id, role=ProjectRole.viewer
        )
        memberships_repo.add(membership)

        # Update role
        membership.role = ProjectRole.editor
        result = memberships_repo.update(membership)

        assert result is not None
        assert result.role == ProjectRole.editor

    def test_list_memberships_by_project(self, test_session):
        """Test listing memberships by project."""
        # Create users and project
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        owner = User(name="owner", email="owner@example.com", password_hash="hash")
        member1 = User(
            name="member1", email="member1@example.com", password_hash="hash"
        )
        member2 = User(
            name="member2", email="member2@example.com", password_hash="hash"
        )
        users_repo.add(owner)
        users_repo.add(member1)
        users_repo.add(member2)

        projects_repo = SqlAlchemyProjectsRepository(session)
        project = Project(owner_id=owner.id, name="Test Project", description="Test")
        projects_repo.add(project)

        # Create memberships
        memberships_repo = SqlAlchemyProjectMembershipsRepository(session)
        membership1 = ProjectMembership(
            project_id=project.id, user_id=member1.id, role=ProjectRole.editor
        )
        membership2 = ProjectMembership(
            project_id=project.id, user_id=member2.id, role=ProjectRole.viewer
        )
        memberships_repo.add(membership1)
        memberships_repo.add(membership2)

        result = memberships_repo.list_by_project(project.id)

        assert len(result) == 2
        assert any(
            m.user_id == member1.id and m.role == ProjectRole.editor for m in result
        )
        assert any(
            m.user_id == member2.id and m.role == ProjectRole.viewer for m in result
        )

    def test_delete_membership_success(self, test_session):
        """Test deleting membership."""
        # Create user and project
        session = test_session
        users_repo = SqlAlchemyUsersRepository(session)
        owner = User(name="owner", email="owner@example.com", password_hash="hash")
        member = User(name="member", email="member@example.com", password_hash="hash")
        users_repo.add(owner)
        users_repo.add(member)

        projects_repo = SqlAlchemyProjectsRepository(session)
        project = Project(owner_id=owner.id, name="Test Project", description="Test")
        projects_repo.add(project)

        # Create and delete membership
        memberships_repo = SqlAlchemyProjectMembershipsRepository(session)
        membership = ProjectMembership(
            project_id=project.id, user_id=member.id, role=ProjectRole.editor
        )
        memberships_repo.add(membership)

        result = memberships_repo.delete(project.id, member.id)

        assert result is True

        # Verify deletion
        deleted_membership = memberships_repo.get(project.id, member.id)
        assert deleted_membership is None

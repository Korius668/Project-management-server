import pytest
from uuid import UUID
from pydantic import ValidationError

from app.domain.models import User, Project, ProjectMembership, ProjectRole


class TestUserModel:
    def test_user_creation_valid(self):
        # When
        user = User(
            email="test@example.com",
            name="testuser",
            password_hash="hashed_password"
        )
        
        # Then
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.name == "testuser"
        assert user.password_hash == "hashed_password"

    def test_user_invalid_email(self):
        # When & Then
        with pytest.raises(ValidationError):
            User(
                email="invalid_email",
                name="testuser",
                password_hash="hashed_password"
            )

    def test_user_name_too_short(self):
        # When & Then
        with pytest.raises(ValidationError):
            User(
                email="test@example.com",
                name="ab",  # Too short (min 3)
                password_hash="hashed_password"
            )

    def test_user_name_too_long(self):
        # When & Then
        with pytest.raises(ValidationError):
            User(
                email="test@example.com",
                name="a" * 20,  # Too long (max 19)
                password_hash="hashed_password"
            )


class TestProjectModel:
    def test_project_creation_valid(self):
        # Given
        owner_id = UUID("12345678-1234-5678-1234-567812345678")
        
        # When
        project = Project(
            owner_id=owner_id,
            name="Test Project",
            description="Test Description"
        )
        
        # Then
        assert isinstance(project.id, UUID)
        assert project.owner_id == owner_id
        assert project.name == "Test Project"
        assert project.description == "Test Description"

    def test_project_optional_description(self):
        # Given
        owner_id = UUID("12345678-1234-5678-1234-567812345678")
        
        # When
        project = Project(
            owner_id=owner_id,
            name="Test Project"
        )
        
        # Then
        assert project.description is None


class TestProjectMembershipModel:
    def test_membership_creation_valid(self):
        # Given
        project_id = UUID("12345678-1234-5678-1234-567812345678")
        user_id = UUID("87654321-4321-8765-4321-876543218765")
        
        # When
        membership = ProjectMembership(
            project_id=project_id,
            user_id=user_id,
            role=ProjectRole.editor
        )
        
        # Then
        assert membership.project_id == project_id
        assert membership.user_id == user_id
        assert membership.role == ProjectRole.editor

    def test_project_role_enum_values(self):
        # Then
        assert ProjectRole.owner == "owner"
        assert ProjectRole.editor == "editor"
        assert ProjectRole.viewer == "viewer"

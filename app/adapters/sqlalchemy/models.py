import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    BigInteger,
    ForeignKey,
    Enum,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

from app.adapters.sqlalchemy.types import UUID
from app.domain.models import ProjectRole

Base = declarative_base()


class UserORM(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("name", name="uq_users_name"),
        UniqueConstraint("name", "email", name="uq_users_name_email"),
    )

    projects = relationship("ProjectORM", back_populates="owner")
    memberships = relationship("ProjectMembershipORM", back_populates="user")


class ProjectORM(Base):
    __tablename__ = "projects"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)

    owner = relationship("UserORM", back_populates="projects")
    memberships = relationship("ProjectMembershipORM", back_populates="project")
    documents = relationship("DocumentORM", back_populates="project")


class ProjectMembershipORM(Base):
    __tablename__ = "project_memberships"

    project_id = Column(UUID, ForeignKey("projects.id"), primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"), primary_key=True)
    role = Column(Enum(ProjectRole), nullable=False)

    project = relationship("ProjectORM", back_populates="memberships")
    user = relationship("UserORM", back_populates="memberships")


class DocumentORM(Base):
    __tablename__ = "documents"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(String, nullable=False)
    metadata_json = Column(JSON)

    __table_args__ = (
        UniqueConstraint("project_id", "filename", name="uq_project_filename"),
    )

    project = relationship("ProjectORM", back_populates="documents")

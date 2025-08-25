import uuid
import enum
from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, Enum, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ProjectRole(str, enum.Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class UserORM(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)

    projects = relationship("ProjectORM", back_populates="owner")
    memberships = relationship("ProjectMembershipORM", back_populates="user")
    documents = relationship("DocumentORM", back_populates="uploader")


class ProjectORM(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)

    owner = relationship("UserORM", back_populates="projects")
    memberships = relationship("ProjectMembershipORM", back_populates="project")
    documents = relationship("DocumentORM", back_populates="project")


class ProjectMembershipORM(Base):
    __tablename__ = "project_memberships"

    project_id = Column(String(36), ForeignKey("projects.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role = Column(Enum(ProjectRole), nullable=False)

    # relacje
    project = relationship("ProjectORM", back_populates="memberships")
    user = relationship("UserORM", back_populates="memberships")


class DocumentORM(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    uploader_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    storage_path = Column(String, nullable=False)
    metadata = Column(JSON)

    # relacje
    project = relationship("ProjectORM", back_populates="documents")
    uploader = relationship("UserORM", back_populates="documents")

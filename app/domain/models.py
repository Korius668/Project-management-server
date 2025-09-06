from enum import Enum
from typing import Annotated, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from uuid import UUID, uuid4


class ProjectRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"


class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    email: EmailStr
    name: Annotated[str, Field(min_length=3, max_length=19)]
    password_hash: str
    model_config = ConfigDict(from_attributes=True)


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class ProjectMembership(BaseModel):
    project_id: UUID
    user_id: UUID
    role: ProjectRole
    model_config = ConfigDict(from_attributes=True)


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    filename: str
    content_type: str
    size_bytes: int = Field(..., ge=0)
    storage_path: str
    metadata: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.domain.models import Project, User, Document, ProjectMembership, ProjectRole


class UserResponse(BaseModel):
    id: str
    name: str
    email: str

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(id=str(user.id), name=user.name, email=user.email)


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=str(project.id),
            name=project.name,
            description=project.description,
            created_at=datetime.now(),
        )


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    uploaded_at: datetime

    @classmethod
    def from_domain(cls, document: Document) -> "DocumentResponse":
        return cls(
            id=str(document.id),
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            storage_path=document.storage_path,
            uploaded_at=datetime.now(),
        )


class MembershipResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str

    @classmethod
    def from_membership_and_user(
        cls, membership: ProjectMembership, user: User
    ) -> "MembershipResponse":
        return cls(
            user_id=str(user.id),
            username=user.name,
            email=user.email,
            role=membership.role.value,
        )


class ProjectInfoResponse(BaseModel):
    project: ProjectResponse
    members: List[MembershipResponse]
    documents: List[DocumentResponse]


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


class UploadDocumentsResponse(BaseModel):
    uploaded_documents: List[DocumentResponse]
    message: str

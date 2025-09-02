from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.models import User, Project, Document, ProjectMembership
from app.ports.repositories import (
    UsersRepository,
    ProjectsRepository,
    DocumentsRepository,
    ProjectMembershipsRepository,
)
from app.adapters.sqlalchemy.models import (
    UserORM,
    ProjectORM,
    DocumentORM,
    ProjectMembershipORM,
)


class SqlAlchemyUsersRepository(UsersRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> User:
        orm = UserORM(
            id=user.id,
            email=user.email,
            name=user.name,
            password_hash=user.password_hash,
        )
        self.session.add(orm)
        self.session.commit()
        return user

    def get(self, user_id: UUID) -> Optional[User]:
        orm = self.session.get(UserORM, user_id)
        return User.model_validate(orm, from_attributes=True) if orm else None

    def list(self) -> List[User]:
        orms = self.session.query(UserORM).all()
        return [User.model_validate(o, from_attributes=True) for o in orms]


class SqlAlchemyProjectsRepository(ProjectsRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, project: Project) -> Project:
        orm = ProjectORM(
            id=project.id,
            owner_id=project.owner_id,
            name=project.name,
            description=project.description,
        )
        self.session.add(orm)
        self.session.commit()
        return project

    def update(self, project: Project) -> Optional[Project]:
        orm = self.session.get(ProjectORM, project.id)
        if not orm:
            return None
        orm.name = project.name
        orm.description = project.description
        self.session.commit()
        return project

    def get(self, project_id: UUID) -> Optional[Project]:
        orm = self.session.get(ProjectORM, project_id)
        return Project.model_validate(orm, from_attributes=True) if orm else None

    def list(self) -> List[Project]:
        orms = self.session.query(ProjectORM).all()
        return [Project.model_validate(o, from_attributes=True) for o in orms]

    def delete(self, project_id: UUID) -> None:
        orm = self.session.get(ProjectORM, project_id)
        if orm:
            self.session.delete(orm)
            self.session.commit()


class SqlAlchemyDocumentsRepository(DocumentsRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, document: Document) -> Document:
        orm = DocumentORM(
            id=document.id,
            project_id=document.project_id,
            uploader_id=document.metadata.get("uploader_id"),
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            storage_path=document.storage_path,
            metadata_json=document.metadata,
        )
        self.session.add(orm)
        self.session.commit()
        return document

    def get(self, document_id: UUID) -> Optional[Document]:
        orm = self.session.get(DocumentORM, document_id)
        return Document.model_validate(orm, from_attributes=True) if orm else None

    def update(self, document: Document) -> Optional[Document]:
        orm = self.session.get(DocumentORM, document.id)
        if not orm:
            return None
        orm.filename = document.filename
        orm.content_type = document.content_type
        orm.size_bytes = document.size_bytes
        orm.storage_path = document.storage_path
        orm.metadata_json = document.metadata
        self.session.commit()
        return document

    def list(self) -> List[Document]:
        orms = self.session.query(DocumentORM).all()
        return [Document.model_validate(o, from_attributes=True) for o in orms]

    def list_with_project_id(self, project_id: UUID) -> List[Document]:
        orms = self.session.query(DocumentORM).filter_by(project_id=project_id).all()
        return [Document.model_validate(o, from_attributes=True) for o in orms]

    def delete(self, document_id: UUID) -> None:
        orm = self.session.get(DocumentORM, document_id)
        if orm:
            self.session.delete(orm)
            self.session.commit()


class SqlAlchemyProjectMembershipsRepository(ProjectMembershipsRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, membership: ProjectMembership) -> ProjectMembership:
        orm = ProjectMembershipORM(
            project_id=membership.project_id,
            user_id=membership.user_id,
            role=membership.role,
        )
        self.session.add(orm)
        self.session.commit()
        return membership

    def list_with_project_id(self, project_id: UUID) -> List[ProjectMembership]:
        orms = (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id)
            .all()
        )
        return [ProjectMembership.model_validate(o, from_attributes=True) for o in orms]

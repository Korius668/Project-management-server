from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.domain.models import User, Project, Document, ProjectMembership, ProjectRole
from app.domain.exceptions import UserAlreadyExistsError, ProjectAlreadyExistsError, DocumentAlreadyExistsError
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
        try:
            self.session.add(orm)
            self.session.commit()
            return user
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e.orig).lower() or "duplicate key" in str(e.orig).lower():
                if "email" in str(e.orig).lower() and  "name" in str(e.orig).lower():
                    raise UserAlreadyExistsError(f"User with name {user.name} and email {user.email} already exists")
                elif "name" in str(e.orig).lower():
                    raise UserAlreadyExistsError(f"User with name {user.name} already exists")
                else:
                    raise UserAlreadyExistsError(f"User with email {user.email} already exists")
            raise

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
        try:
            self.session.add(orm)
            self.session.commit()
            return project
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e.orig).lower() or "duplicate key" in str(e.orig).lower():
                raise ProjectAlreadyExistsError(f"Project with name {project.name} already exists")
            raise

    def update(self, project: Project) -> Optional[Project]:
        orm = self.session.get(ProjectORM, project.id)
        if not orm:
            return None
        try:
            orm.name = project.name
            orm.description = project.description
            self.session.commit()
            return project
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e.orig).lower() or "duplicate key" in str(e.orig).lower():
                raise ProjectAlreadyExistsError(f"Project with name {project.name} already exists")
            raise

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
            filename=document.filename,
            content_type=document.content_type,
            size_bytes=document.size_bytes,
            storage_path=document.storage_path,
            metadata_json=document.metadata,
        )
        try:
            self.session.add(orm)
            self.session.commit()
            return document
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e.orig).lower() or "duplicate key" in str(e.orig).lower():
                raise DocumentAlreadyExistsError(f"Document with name {document.filename} already exists in project {document.project_id}")
            raise

    def get(self, document_id: UUID) -> Optional[Document]:
        orm = self.session.get(DocumentORM, document_id)
        return Document.model_validate(orm, from_attributes=True) if orm else None

    def update(self, document: Document) -> Optional[Document]:
        orm = self.session.get(DocumentORM, document.id)
        if not orm:
            return None
        try:
            orm.filename = document.filename
            orm.content_type = document.content_type
            orm.size_bytes = document.size_bytes
            orm.storage_path = document.storage_path
            orm.metadata_json = document.metadata
            self.session.commit()
            return document
        except IntegrityError as e:
            self.session.rollback()
            if "unique constraint" in str(e.orig).lower() or "duplicate key" in str(e.orig).lower():
                raise DocumentAlreadyExistsError(f"Document with name {document.filename} already exists in project {document.project_id}")
            raise

    def list(self) -> List[Document]:
        orms = self.session.query(DocumentORM).all()
        return [Document.model_validate(o, from_attributes=True) for o in orms]

    def list_by_project(self, project_id: UUID) -> List[Document]:
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
        """Add or update membership - if exists, update the role"""
        orm = ProjectMembershipORM(
        project_id=membership.project_id,
        user_id=membership.user_id,
        role=membership.role
        )
        
        self.session.merge(orm)
        self.session.commit()
        return membership

    def get(self, project_id: UUID, user_id: UUID) -> Optional[ProjectMembership]:
        orm = self.session.query(ProjectMembershipORM).filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        return ProjectMembership.model_validate(orm, from_attributes=True) if orm else None

    def update(self, membership: ProjectMembership) -> Optional[ProjectMembership]:
        orm = self.session.query(ProjectMembershipORM).filter_by(
            project_id=membership.project_id,
            user_id=membership.user_id
        ).first()
        
        if not orm:
            return None
            
        orm.role = membership.role
        self.session.commit()
        return membership

    def list(self):
        """Return all memberships"""
        orms = self.session.query(ProjectMembershipORM).all()
        return [ProjectMembership.model_validate(orm, from_attributes=True) for orm in orms]


    def list_by_project(self, project_id) -> List[ProjectMembership]:
        """Return all memberships for a project"""
        orms = self.session.query(ProjectMembershipORM).filter_by(
            project_id=project_id
        ).all()
        return [ProjectMembership.model_validate(orm, from_attributes=True) for orm in orms]

    def list_by_user(self, user_id) -> List[ProjectMembership]:
        """Return all memberships for a user"""
        orms = self.session.query(ProjectMembershipORM).filter_by(
            user_id=user_id
        ).all()
        return [ProjectMembership.model_validate(orm, from_attributes=True) for orm in orms]
    

    def delete(self, project_id: UUID, user_id: UUID) -> bool:
        result = self.session.query(ProjectMembershipORM).filter_by(
            project_id=project_id,
            user_id=user_id
        ).delete()
        self.session.commit()
        return result > 0

    def delete_by_project(self, project_id: UUID) -> int:
        count = self.session.query(ProjectMembershipORM).filter_by(
            project_id=project_id
        ).delete()
        self.session.commit()
        return count

    def delete_by_user(self, user_id: UUID) -> int:
        """Delete all memberships for a user. Returns count of deleted items"""
        count = self.session.query(ProjectMembershipORM).filter_by(
            user_id=user_id
        ).delete()
        self.session.commit()
        return count

    def exists(self, project_id: UUID, user_id: UUID) -> bool:
        return self.session.query(
            self.session.query(ProjectMembershipORM).filter_by(
                project_id=project_id,
                user_id=user_id
            ).exists()
        ).scalar()
    
    def count_by_project(self, project_id: UUID) -> int:
        """Count members in a project"""
        return self.session.query(ProjectMembershipORM).filter_by(
            project_id=project_id
        ).count()
    
    def get_user_role(self, project_id: UUID, user_id: UUID) -> Optional[ProjectRole]:
        orm = self.session.query(ProjectMembershipORM).filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        return ProjectRole(orm.role) if orm else None

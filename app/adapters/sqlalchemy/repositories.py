from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.domain.models import User, Project, Document, ProjectMembership, ProjectRole
from app.domain.exceptions import (
    UserAlreadyExistsError,
    ProjectAlreadyExistsError,
    DocumentAlreadyExistsError,
    DatabaseError,
    UserDeletionForbiddenError,
    UserNotFoundError,
    ProjectNotFoundError,
    DocumentNotFoundError,
)
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
        attempt = 0
        max_attempts = 3  # żeby uniknąć nieskończonej pętli (teoretycznie niepotrzebne, ale to dobra praktyka)

        while attempt < max_attempts:
            try:
                orm = UserORM(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    password_hash=user.password_hash,
                )
                self.session.add(orm)
                self.session.commit()
                return user
            
            except IntegrityError as e:
                self.session.rollback()

                constraint_name = getattr(getattr(e.orig, "diag", None), "constraint_name", None)
                if constraint_name == "users_pkey" or "primary" in str(e.orig).lower():
                    attempt += 1
                    import uuid
                    user.id = uuid.uuid4()
                    continue
                if constraint_name == "uq_users_email":
                    raise UserAlreadyExistsError(f"User with email {user.email} already exists")
                if constraint_name == "uq_users_name":
                    raise UserAlreadyExistsError(f"User with name {user.name} already exists")
                if "unique" in str(e.orig).lower() or "duplicate" in str(e.orig).lower():
                    if "email" in str(e.orig).lower():
                        raise UserAlreadyExistsError(f"User with email {user.email} already exists")
                    if "name" in str(e.orig).lower():
                        raise UserAlreadyExistsError(f"User with name {user.name} already exists")

                raise
        raise DatabaseError(f"Could not generate unique ID after {max_attempts} attempts")
        
    def get(self, user_id: UUID) -> Optional[User]:
        try:
            orm = self.session.get(UserORM, user_id)
            if orm:
                return User.model_validate(orm, from_attributes=True)
            return None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during user retrieval: {e}")

    def list(self) -> List[User]:
        try:
            orms = self.session.query(UserORM).all()
            return [User.model_validate(o, from_attributes=True) for o in orms]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during user listing: {e}")

    def delete(self, user_id: UUID) -> None:
        try:
            count = self.session.query(UserORM).filter_by(id=user_id).delete()
            if count == 0:
                raise UserNotFoundError(f"User with id {user_id} not found")
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise UserDeletionForbiddenError(
                f"User {user_id} cannot be deleted due to existing related records"
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error during user deletion: {e}")


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

            constraint_name = getattr(
                getattr(e.orig, "diag", None), "constraint_name", None
            )

            if constraint_name == "uq_projects_name":
                raise ProjectAlreadyExistsError(
                    f"Project with name {project.name} already exists"
                )

            msg = str(e.orig).lower()
            if "unique" in msg or "duplicate" in msg:
                if "name" in msg:
                    raise ProjectAlreadyExistsError(
                        f"Project with name {project.name} already exists"
                    )
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Unexpected database error: {e}")

    def update(self, project: Project) -> Optional[Project]:
        try:
            orm = self.session.get(ProjectORM, project.id)
            if not orm:
                raise ProjectNotFoundError(f"Project with id {project.id} not found")

            orm.name = project.name
            orm.description = project.description
            self.session.commit()
            return project
        except IntegrityError as e:
            self.session.rollback()
            constraint_name = getattr(
                getattr(e.orig, "diag", None), "constraint_name", None
            )

            if constraint_name == "uq_projects_name":
                raise ProjectAlreadyExistsError(
                    f"Project with name {project.name} already exists"
                )

            msg = str(e.orig).lower()
            if "unique" in msg or "duplicate" in msg:
                if "name" in msg:
                    raise ProjectAlreadyExistsError(
                        f"Project with name {project.name} already exists"
                    )
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Unexpected database error during update: {e}")

    def get(self, project_id: UUID) -> Optional[Project]:
        try:
            orm = self.session.get(ProjectORM, project_id)
            return Project.model_validate(orm, from_attributes=True) if orm else None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during fetching project: {e}")

    def list(self) -> List[Project]:
        try:
            orms = self.session.query(ProjectORM).all()
            return [Project.model_validate(o, from_attributes=True) for o in orms]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during listing projects: {e}")

    def delete(self, project_id: UUID) -> None:
        try:
            orm = self.session.get(ProjectORM, project_id)
            if not orm:
                raise ProjectNotFoundError(f"Project with id {project_id} not found")

            self.session.delete(orm)
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            # W razie gdy nie można usunąć z powodu FK
            raise DatabaseError(
                f"Cannot delete project {project_id} due to DB constraints: {e}"
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(f"Database error during deleting project: {e}")


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

            # stabilna identyfikacja constraintu
            constraint_name = getattr(
                getattr(e.orig, "diag", None), "constraint_name", None
            )
            if constraint_name == "uq_project_filename":
                raise DocumentAlreadyExistsError(
                    f"Document with name {document.filename} already exists in project {document.project_id}"
                )

            msg = str(e.orig).lower()
            if "unique" in msg or "duplicate" in msg:
                if "filename" in msg or "project_id" in msg:
                    raise DocumentAlreadyExistsError(
                        f"Document with name {document.filename} already exists in project {document.project_id}"
                    )

            raise DatabaseError("Database integrity error during adding document")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                f"Unexpected database error during adding document: {e}"
            )

    def get(self, document_id: UUID) -> Optional[Document]:
        try:
            orm = self.session.get(DocumentORM, document_id)
            if not orm:
                raise DocumentNotFoundError(f"Document with id {document_id} not found")
            else: 
                return Document.model_validate(orm, from_attributes=True)
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database error during fetching document {document_id}: {e}"
            )

    def update(self, document: Document) -> Optional[Document]:
        try:
            orm = self.session.get(DocumentORM, document.id)
            if not orm:
                raise DocumentNotFoundError(f"Document with id {document.id} not found")

            orm.filename = document.filename
            orm.content_type = document.content_type
            orm.size_bytes = document.size_bytes
            orm.storage_path = document.storage_path
            orm.metadata_json = document.metadata
            self.session.commit()
            return document
        except IntegrityError as e:
            self.session.rollback()

            constraint_name = getattr(
                getattr(e.orig, "diag", None), "constraint_name", None
            )
            if constraint_name == "uq_project_filename":
                raise DocumentAlreadyExistsError(
                    f"Document with name {document.filename} already exists in project {document.project_id}"
                )

            msg = str(e.orig).lower()
            if "unique" in msg or "duplicate" in msg:
                if "filename" in msg or "project_id" in msg:
                    raise DocumentAlreadyExistsError(
                        f"Document with name {document.filename} already exists in project {document.project_id}"
                    )

            raise DatabaseError("Database integrity error during updating document")
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                f"Unexpected database error during updating document: {e}"
            )

    def list(self) -> List[Document]:
        try:
            orms = self.session.query(DocumentORM).all()
            return [Document.model_validate(o, from_attributes=True) for o in orms]
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error during listing documents: {e}")

    def list_by_project(self, project_id: UUID) -> List[Document]:
        try:
            orms = (
                self.session.query(DocumentORM).filter_by(project_id=project_id).all()
            )
            return [Document.model_validate(o, from_attributes=True) for o in orms]
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Database error during listing documents for project {project_id}: {e}"
            )

    def delete(self, document_id: UUID) -> None:
        try:
            orm = self.session.get(DocumentORM, document_id)
            if not orm:
                raise DocumentNotFoundError(f"Document with id {document_id} not found")

            self.session.delete(orm)
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise DatabaseError(
                f"Cannot delete document {document_id} due to database constraints: {e}"
            )
        except SQLAlchemyError as e:
            self.session.rollback()
            raise DatabaseError(
                f"Database error during deleting document {document_id}: {e}"
            )


class SqlAlchemyProjectMembershipsRepository(ProjectMembershipsRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, membership: ProjectMembership) -> ProjectMembership:
        """Add or update membership - if exists, update the role"""
        orm = ProjectMembershipORM(
            project_id=membership.project_id,
            user_id=membership.user_id,
            role=membership.role,
        )

        self.session.merge(orm)
        self.session.commit()
        return membership

    def get(self, project_id: UUID, user_id: UUID) -> Optional[ProjectMembership]:
        orm = (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id, user_id=user_id)
            .first()
        )
        return (
            ProjectMembership.model_validate(orm, from_attributes=True) if orm else None
        )

    def update(self, membership: ProjectMembership) -> Optional[ProjectMembership]:
        orm = (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=membership.project_id, user_id=membership.user_id)
            .first()
        )

        if not orm:
            return None

        orm.role = membership.role
        self.session.commit()
        return membership

    def list(self):
        """Return all memberships"""
        orms = self.session.query(ProjectMembershipORM).all()
        return [
            ProjectMembership.model_validate(orm, from_attributes=True) for orm in orms
        ]

    def list_by_project(self, project_id) -> List[ProjectMembership]:
        """Return all memberships for a project"""
        orms = (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id)
            .all()
        )
        return [
            ProjectMembership.model_validate(orm, from_attributes=True) for orm in orms
        ]

    def list_by_user(self, user_id) -> List[ProjectMembership]:
        """Return all memberships for a user"""
        orms = self.session.query(ProjectMembershipORM).filter_by(user_id=user_id).all()
        return [
            ProjectMembership.model_validate(orm, from_attributes=True) for orm in orms
        ]

    def delete(self, project_id: UUID, user_id: UUID) -> bool:
        result = (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id, user_id=user_id)
            .delete()
        )
        self.session.commit()
        return result > 0

    def delete_by_project(self, project_id: UUID) -> int:
        count = (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id)
            .delete()
        )
        self.session.commit()
        return count

    def delete_by_user(self, user_id: UUID) -> int:
        """Delete all memberships for a user. Returns count of deleted items"""
        count = (
            self.session.query(ProjectMembershipORM).filter_by(user_id=user_id).delete()
        )
        self.session.commit()
        return count

    def exists(self, project_id: UUID, user_id: UUID) -> bool:
        return self.session.query(
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id, user_id=user_id)
            .exists()
        ).scalar()

    def count_by_project(self, project_id: UUID) -> int:
        """Count members in a project"""
        return (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id)
            .count()
        )

    def get_user_role(self, project_id: UUID, user_id: UUID) -> Optional[ProjectRole]:
        orm = (
            self.session.query(ProjectMembershipORM)
            .filter_by(project_id=project_id, user_id=user_id)
            .first()
        )
        return ProjectRole(orm.role) if orm else None

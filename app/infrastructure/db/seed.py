import uuid
from sqlalchemy.orm import Session

from app.infrastructure.db.db import SessionLocal
from app.adapters.sqlalchemy.repositories import (
    SqlAlchemyUsersRepository,
    SqlAlchemyProjectsRepository,
    SqlAlchemyDocumentsRepository,
    SqlAlchemyProjectMembershipsRepository,
)
from app.domain.models import User, Project, Document, ProjectMembership
from app.logger.logger import logger


def seed_database():
    logger.info("🌱 Seeding database with example data...")
    session: Session = SessionLocal()

    try:
        users_repo = SqlAlchemyUsersRepository(session)
        projects_repo = SqlAlchemyProjectsRepository(session)
        documents_repo = SqlAlchemyDocumentsRepository(session)
        memberships_repo = SqlAlchemyProjectMembershipsRepository(session)

        # --- USERS ---
        user1 = User(
            id=uuid.uuid4(),
            email="alice@example.com",
            name="Alice",
            password_hash="hashed_pw_alice",
        )
        user2 = User(
            id=uuid.uuid4(),
            email="bob@example.com",
            name="Bobo",
            password_hash="hashed_pw_bob",
        )
        user3 = User(
            id=uuid.uuid4(),
            email="charlie@example.com",
            name="Charlie",
            password_hash="hashed_pw_charlie",
        )
        users_repo.add(user1)
        users_repo.add(user2)
        users_repo.add(user3)

        # --- PROJECTS ---
        project1 = Project(
            id=uuid.uuid4(),
            owner_id=user1.id,
            name="Backend Refactor",
            description="Rewrite core services with FastAPI",
        )
        project2 = Project(
            id=uuid.uuid4(),
            owner_id=user2.id,
            name="Mobile App",
            description="Flutter client for project management",
        )
        projects_repo.add(project1)
        projects_repo.add(project2)

        # --- DOCUMENTS ---
        doc1 = Document(
            id=uuid.uuid4(),
            project_id=project1.id,
            filename="requirements.txt",
            content_type="text/plain",
            size_bytes=123,
            storage_path="/files/requirements.txt",
            metadata={"uploader_id": str(user1.id)},
        )
        doc2 = Document(
            id=uuid.uuid4(),
            project_id=project2.id,
            filename="design.pdf",
            content_type="application/pdf",
            size_bytes=4096,
            storage_path="/files/design.pdf",
            metadata={"uploader_id": str(user2.id)},
        )
        documents_repo.add(doc1)
        documents_repo.add(doc2)

        # --- MEMBERSHIPS ---
        membership1 = ProjectMembership(
            project_id=project1.id, user_id=user1.id, role="owner"
        )
        membership2 = ProjectMembership(
            project_id=project1.id, user_id=user2.id, role="editor"
        )
        membership3 = ProjectMembership(
            project_id=project2.id, user_id=user2.id, role="owner"
        )
        membership4 = ProjectMembership(
            project_id=project2.id, user_id=user3.id, role="viewer"
        )
        memberships_repo.add(membership1)
        memberships_repo.add(membership2)
        memberships_repo.add(membership3)
        memberships_repo.add(membership4)

        logger.info("✅ Seeding completed successfully")

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from app.config import settings
from app.logger.logger import logger


if not settings:
    raise RuntimeError("⚠️ Settings must be initialized before importing db!")

try:
    engine = create_engine(
        settings.database_url,
        echo=not settings.is_production,
        connect_args=(
            {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        ),
    )
except OperationalError as e:
    logger.error(
        f"❌ Cannot connect DB ({settings.database_url}): {e}", file=sys.stderr
    )
    sys.exit(1)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

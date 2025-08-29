import os
from alembic import command
from alembic.config import Config
from app.logger.logger import logger


def run_migrations():
    """
    Run Alembic migrations programmatically.
    """
    try:
        alembic_cfg = Config("alembic.ini")
        db_url = os.getenv("DATABASE_URL", None)
        if db_url:
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)

        command.upgrade(alembic_cfg, "head")
        logger.info("✅ Database migrations applied successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to run migrations: {e}")
        raise

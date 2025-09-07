from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from app.config import settings, Settings, secrets
from app.logger.logger import logger

if not settings:
    settings = Settings(app_env="development", secrets=secrets)


try:
    engine_kwargs = {
        "echo": not settings.is_production,
        "pool_size": 10,  # Number of connections to maintain in pool
        "max_overflow": 20,  # Additional connections when pool is full
        "pool_timeout": 30,  # Seconds to wait for connection from pool
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Validate connections before use
    }

    if "sqlite" in settings.database_url:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        # Remove pooling for SQLite as it doesn't support it well
        engine_kwargs.pop("pool_size")
        engine_kwargs.pop("max_overflow")
        engine_kwargs.pop("pool_timeout")
        engine_kwargs.pop("pool_recycle")
        engine_kwargs.pop("pool_pre_ping")

    engine = create_engine(settings.database_url, **engine_kwargs)

except OperationalError as e:
    logger.error(f"❌ Cannot connect DB ({settings.database_url}): {e}")
    raise RuntimeError(f"Database connection failed: {e}") from e

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,  # Prevents lazy loading issues after commit
)


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

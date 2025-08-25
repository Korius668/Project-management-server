import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.adapters.sqlalchemy.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """Używane tylko w dev (w produkcji Alembic)."""
    Base.metadata.create_all(bind=engine)

"""SQLAlchemy engine & session factory."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Single declarative base for all models."""
    pass


def get_db():
    """FastAPI dependency — yields a DB session, ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

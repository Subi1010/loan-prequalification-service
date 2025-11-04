"""
Database configuration and session management using SQLAlchemy.
"""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session]:
    """
    Dependency function that provides a database session.

    Yields:
        Session: SQLAlchemy database session

    Example:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Type alias for FastAPI dependency injection
db_dependency = Annotated[Session, Depends(get_db)]


def check_database_health() -> dict[str, bool]:
    """
    Check if the database is healthy by executing a simple query.

    Returns:
        Dict with database health status
    """
    try:
        # Create a new session
        db = SessionLocal()
        try:
            # Execute a simple query
            db.execute(text("SELECT 1"))
            logger.info("Database health check: OK")
            return {"database": True}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"database": False}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        return {"database": False}

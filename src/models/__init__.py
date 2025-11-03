"""
SQLAlchemy ORM models for the loan prequalification service.
"""

from src.core.database import Base
from src.models.application import Applications

__all__ = ["Base", "Applications"]

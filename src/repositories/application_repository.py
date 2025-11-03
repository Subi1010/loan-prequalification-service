"""
Repository for Application data access operations.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.core.app_status import ApplicationStatus
from src.models import Applications
from src.schemas.application import ApplicationCreate


class ApplicationRepository:
    """
    Repository pattern implementation for Application entity.
    Handles all database operations for loan applications.
    """

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(self, application_data: ApplicationCreate) -> Applications:
        """
        Create a new loan application in the database.

        Args:
            application_data: Application creation data

        Returns:
            Created application model instance
        """
        db_application = Applications(
            **application_data.model_dump(),
            status=ApplicationStatus.PENDING.value,
        )
        self.db.add(db_application)
        self.db.commit()
        self.db.refresh(db_application)
        return db_application

    def get_by_id(self, application_id: UUID) -> Applications | None:
        """
        Retrieve an application by its ID.

        Args:
            application_id: UUID of the application

        Returns:
            Application model instance if found, None otherwise
        """
        return (
            self.db.query(Applications)
            .filter(Applications.id == application_id)
            .first()
        )

    def update_cibil_and_status(
        self, application_id: UUID, cibil_score: int, status: ApplicationStatus
    ) -> Applications | None:
        """
        Update both CIBIL score and status in a single transaction.

        Args:
            application_id: UUID of the application
            cibil_score: Calculated CIBIL score
            status: New application status

        Returns:
            Updated application if found, None otherwise
        """
        application = self.get_by_id(application_id)
        if application:
            application.cibil_score = cibil_score
            application.status = status.value
            application.updated_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(application)
        return application

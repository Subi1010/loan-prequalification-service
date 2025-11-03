"""
Business logic layer for loan application operations.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from src.core.logging_config import get_logger
from src.kafka.kafka_producer import MessageProducer
from src.models import Applications
from src.repositories.application_repository import ApplicationRepository
from src.schemas.application import ApplicationCreate, ApplicationStatusResponse


class ApplicationService:
    """
    Service layer for loan application business logic.
    Handles application creation, retrieval, and Kafka publishing.
    """

    def __init__(self, db: Session):
        """
        Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.repository = ApplicationRepository(db)
        self.logger = get_logger(__name__)

    def create_application(
        self, application_data: ApplicationCreate, kafka_topic: str
    ) -> Applications:
        """
        Create a new loan application and publish to Kafka.

        Args:
            application_data: Application creation data
            kafka_topic: Kafka topic to publish the application

        Returns:
            Created application instance

        Raises:
            Exception: If application creation fails
        """
        # Create application in database
        db_application = self.repository.create(application_data)

        self.logger.info(
            f"Created application {db_application.id} for applicant {db_application.applicant_name}"
        )

        # Prepare application data for Kafka
        kafka_message = self._prepare_kafka_message(db_application)

        # Send application data to Kafka
        kafka_result = MessageProducer.produce_message(
            kafka_topic, str(db_application.id), kafka_message
        )

        if not kafka_result:
            self.logger.warning(
                f"Failed to send application {db_application.id} to Kafka. "
                "CIBIL score calculation may be delayed."
            )

        return db_application

    def get_application_status(
        self, application_id: UUID
    ) -> ApplicationStatusResponse | None:
        """
        Retrieve application status by ID.

        Args:
            application_id: UUID of the application

        Returns:
            ApplicationStatusResponse with ID and status if found, None otherwise
        """
        application = self.repository.get_by_id(application_id)
        if not application:
            return None

        return ApplicationStatusResponse(
            application_id=application.id,
            status=application.status,
        )

    @staticmethod
    def _prepare_kafka_message(application: Applications) -> dict:
        """
        Prepare application data for Kafka message.

        Args:
            application: Application model instance

        Returns:
            Dictionary with serialized application data
        """
        return {
            "id": str(application.id),
            "pan_number": application.pan_number,
            "applicant_name": application.applicant_name,
            "monthly_income_inr": float(application.monthly_income_inr),
            "loan_amount_inr": float(application.loan_amount_inr),
            "loan_type": application.loan_type,
            "status": application.status,
            "created_at": application.created_at.isoformat(),
            "updated_at": application.updated_at.isoformat(),
        }

"""
Decision service for loan application approval logic.
"""

import json
import uuid
from uuid import UUID

from src.core.app_status import ApplicationStatus
from src.core.constants import LOAN_TERM_MONTHS, MIN_CIBIL_SCORE_FOR_APPROVAL
from src.core.database import SessionLocal
from src.core.logging_config import get_logger
from src.repositories.application_repository import ApplicationRepository

logger = get_logger(__name__)


class DecisionService:
    """
    Service for making loan application decisions based on CIBIL score and affordability.

    Business Rules:
    - CIBIL < 650: Rejected
    - CIBIL >= 650 and EMI affordable (income > loan_amount/48): Pre-approved
    - CIBIL >= 650 and EMI not affordable: Manual review
    """

    @staticmethod
    def determine_status(
        cibil_score: int, monthly_income: float, loan_amount: float
    ) -> ApplicationStatus:
        """
        Determine application status based on CIBIL score and affordability.

        Args:
            cibil_score: Applicant's CIBIL score
            monthly_income: Monthly income in INR
            loan_amount: Requested loan amount in INR

        Returns:
            ApplicationStatus enum value
        """
        if cibil_score < MIN_CIBIL_SCORE_FOR_APPROVAL:
            return ApplicationStatus.REJECTED

        # Calculate if EMI is affordable (simple calculation)
        affordable_monthly_payment = loan_amount / LOAN_TERM_MONTHS

        if monthly_income > affordable_monthly_payment:
            return ApplicationStatus.PRE_APPROVED
        else:
            return ApplicationStatus.MANUAL_REVIEW

    @staticmethod
    def process_decision(
        application_id: UUID, cibil_score: int, application_data: dict
    ) -> bool:
        """
        Process loan application decision and update database.

        Args:
            application_id: UUID of the application
            cibil_score: Calculated CIBIL score
            application_data: Dictionary containing application details

        Returns:
            True if successful, False otherwise
        """
        db = SessionLocal()
        try:
            monthly_income_inr = float(application_data.get("monthly_income_inr", 0))
            loan_amount_inr = float(application_data.get("loan_amount_inr", 0))

            # Convert string UUID to UUID object if needed
            if isinstance(application_id, str):
                application_id = uuid.UUID(application_id)

            # Determine status based on business rules
            status = DecisionService.determine_status(
                cibil_score, monthly_income_inr, loan_amount_inr
            )

            # Update application in database
            repository = ApplicationRepository(db)
            application = repository.update_cibil_and_status(
                application_id, cibil_score, status
            )

            if not application:
                logger.error(f"Application with ID {application_id} not found")
                return False

            logger.info(
                f"Updated application {application_id}: CIBIL={cibil_score}, Status={status.value}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error processing decision for application {application_id}: {e}"
            )
            return False

        finally:
            db.close()


def handle_cibil_score_event(message) -> bool:
    """
    Handle Kafka message for CIBIL score calculation event.

    Args:
        message: Kafka message containing CIBIL score data

    Returns:
        True if processed successfully, False otherwise
    """
    try:
        # Parse message value
        cibil_data = json.loads(message.value)
        application_id = cibil_data.get("application_id")
        cibil_score = cibil_data.get("cibil_score")
        application_data = cibil_data.get("application_data")

        if not application_id or cibil_score is None:
            logger.error("Message does not contain application ID or CIBIL score")
            return False

        logger.info(
            f"Processing CIBIL score for application {application_id}: {cibil_score}"
        )

        # Process decision
        update_result = DecisionService.process_decision(
            application_id, cibil_score, application_data
        )
        return update_result

    except Exception as e:
        logger.error(f"Error processing CIBIL score message: {e}")
        return False

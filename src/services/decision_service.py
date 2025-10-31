import json
import uuid
from datetime import UTC, datetime

from src.core.app_status import ApplicationStatus
from src.core.logging_config import logger
from src.database import SessionLocal
from src.models import Applications


def decision_maker(application_id, cibil_score, application_data):
    try:
        monthly_income_inr = float(application_data.get("monthly_income_inr", 0))
        loan_amount_inr = float(application_data.get("loan_amount_inr", 0))

        db = SessionLocal()

        # Convert string UUID to UUID object if needed
        if isinstance(application_id, str):
            application_id = uuid.UUID(application_id)

        # Get the application
        application = (
            db.query(Applications).filter(Applications.id == application_id).first()
        )

        if not application:
            logger.error(f"Application with ID {application_id} not found")
            return False

        # Update CIBIL score
        application.cibil_score = cibil_score

        # Determine new status based on CIBIL score
        if cibil_score < 650:
            application.status = ApplicationStatus.REJECTED.value
        elif cibil_score >= 650 and monthly_income_inr > (loan_amount_inr / 48):
            application.status = ApplicationStatus.PRE_APPROVED.value
        elif cibil_score >= 650 and monthly_income_inr <= (loan_amount_inr / 48):
            application.status = ApplicationStatus.MANUAL_REVIEW.value

        application.updated_at = datetime.now(UTC)

        db.commit()
        logger.info(
            f"Updated CIBIL score for application {application_id} to {cibil_score}"
        )
        return True

    except Exception as e:
        logger.error(
            f"Error updating CIBIL score for application {application_id}: {e}"
        )
        return False

    finally:
        db.close()


def handle_cibil_score_event(message):
    try:
        # Parse message value
        cibil_data = json.loads(message.value.decode("utf-8"))
        application_id = cibil_data.get("application_id")
        cibil_score = cibil_data.get("cibil_score")
        application_data = cibil_data.get("application_data")

        if not application_id or cibil_score is None:
            logger.error("Message does not contain application ID or CIBIL score")
            return False

        logger.info(
            f"Processing CIBIL score for application {application_id}: {cibil_score}"
        )

        # Update application in database
        update_result = decision_maker(application_id, cibil_score, application_data)
        return update_result

    except Exception as e:
        logger.error(f"Error processing CIBIL score message: {e}")
        return False

import json
import logging
import random
import uuid
from datetime import datetime, timezone
from src.database import SessionLocal
from src.models import Applications


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def decision_maker(application_id, cibil_score, application_data):


    try:

        monthly_income_inr = float(application_data.get('monthly_income_inr', 0))
        loan_amount_inr = float(application_data.get('loan_amount_inr', 0))

        db = SessionLocal()

        # Convert string UUID to UUID object if needed
        if isinstance(application_id, str):
            application_id = uuid.UUID(application_id)

        # Get the application
        application = db.query(Applications).filter(Applications.id == application_id).first()

        if not application:
            logger.error(f"Application with ID {application_id} not found")
            return False

        # Update CIBIL score
        application.cibil_score = cibil_score


        # Determine new status based on CIBIL score
        if cibil_score <650:
            application.status = 'rejected'
        elif cibil_score >= 650 and monthly_income_inr > ( loan_amount_inr / 48):
            application.status = 'pre_approved'
        elif cibil_score >= 650 and monthly_income_inr <= ( loan_amount_inr / 48):
            application.status = 'manual_review'

        application.updated_at = datetime.now(timezone.utc)

        db.commit()
        logger.info(f"Updated CIBIL score for application {application_id} to {cibil_score}")
        return True

    except Exception as e:
        logger.error(f"Error updating CIBIL score for application {application_id}: {e}")
        return False

    finally:
        db.close()


def handle_cibil_score_event(message):

    try:
        # Parse message value
        cibil_data = json.loads(message.value.decode('utf-8'))
        application_id = cibil_data.get('application_id')
        cibil_score = cibil_data.get('cibil_score')
        application_data = cibil_data.get('application_data')

        if not application_id or cibil_score is None:
            logger.error("Message does not contain application ID or CIBIL score")
            return False

        logger.info(f"Processing CIBIL score for application {application_id}: {cibil_score}")

        # Update application in database
        update_result = decision_maker(application_id, cibil_score,application_data)
        return update_result

    except Exception as e:
        logger.error(f"Error processing CIBIL score message: {e}")
        return False

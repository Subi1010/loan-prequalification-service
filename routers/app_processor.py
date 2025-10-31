import json
import logging
import random
import uuid
from datetime import datetime, timezone
from database import SessionLocal
from models import Applications
import config as config
from kafka_service.kafka_producer import send_data_to_kafka

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_cibil_score(application_data):
    pan_number = application_data.get('pan_number', None)
    match pan_number:
        case "ABCDE1234F":
            return 790
        case "FGHIJ5678K":
            return 610

    # Extract relevant data for calculation
    monthly_income = float(application_data.get('monthly_income_inr', 0))
    loan_type = application_data.get('loan_type', '').upper()

    # Start with base score
    score = 650

    # Adjust based on income
    if monthly_income > 75000:
        score += 40
    elif monthly_income < 30000:
        score -= 20

    # Adjust based on loan type
    if loan_type == "PERSONAL":
        score -= 10  # Unsecured loan
    elif loan_type == "HOME":
        score += 10  # Secured loan

    # Add small random factor for realism
    random_factor = random.randint(-5, 5)
    score += random_factor

    # Ensure score is within valid range
    final_score = max(300, min(900, score))

    logger.info(f"CIBIL score calculation: base=650, income_adj={'+40' if monthly_income > 75000 else '-20' if monthly_income < 30000 else '0'}, "
              f"loan_type_adj={'-10' if loan_type == 'PERSONAL' else '+10' if loan_type == 'HOME' else '0'}, "
              f"random={random_factor}, final={final_score}")

    return final_score

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

def handle_application_event(message):

    try:
        # Parse message value
        application_data = json.loads(message.value.decode('utf-8'))
        application_id = application_data.get('id')

        if not application_id:
            logger.error("Message does not contain application ID")
            return False

        logger.info(f"Processing application {application_id}")

        # Calculate CIBIL score
        cibil_score = calculate_cibil_score(application_data)
        logger.info(f"Calculated CIBIL score for application {application_id}: {cibil_score}")

        send_data_to_kafka(application_id, {"application_id":application_id,"cibil_score": cibil_score,"application_data":application_data}, config.LOAN_APPLICATIONS_TOPIC[1])

        return True

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return False

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

TOPIC_HANDLERS = {
    "loan_applications_submitted": handle_application_event,
    "credit_reports_generated": handle_cibil_score_event,
}

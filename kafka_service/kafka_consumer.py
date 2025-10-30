import json
import logging
import random
import threading
import uuid
from datetime import UTC, datetime

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

import kafka_service.kafka_utils as kafka_utils
from database import SessionLocal
from models import Applications

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_cibil_score(application_data):
    pan_number = application_data.get("pan_number", None)
    match pan_number:
        case "ABCDE1234F":
            return 790
        case "FGHIJ5678K":
            return 610

    # Extract relevant data for calculation
    monthly_income = float(application_data.get("monthly_income_inr", 0))
    loan_type = application_data.get("loan_type", "").upper()

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

    logger.info(
        f"CIBIL score calculation: base=650, income_adj={'+40' if monthly_income > 75000 else '-20' if monthly_income < 30000 else '0'}, "
        f"loan_type_adj={'-10' if loan_type == 'PERSONAL' else '+10' if loan_type == 'HOME' else '0'}, "
        f"random={random_factor}, final={final_score}"
    )

    return final_score


def update_application_cibil_score(application_id, cibil_score):
    try:
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
        application.updated_at = datetime.now(UTC)

        """ # Determine new status based on CIBIL score
        if cibil_score >= 750:
            application.status = 'pre_approved'
        elif cibil_score >= 600:
            application.status = 'manual_review'
        else:
            application.status = 'rejected'
"""
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


def process_message(message):
    try:
        # Parse message value
        application_data = json.loads(message.value.decode("utf-8"))
        application_id = application_data.get("id")

        if not application_id:
            logger.error("Message does not contain application ID")
            return False

        logger.info(f"Processing application {application_id}")

        # Calculate CIBIL score
        cibil_score = calculate_cibil_score(application_data)
        logger.info(
            f"Calculated CIBIL score for application {application_id}: {cibil_score}"
        )

        # Update application in database
        update_result = update_application_cibil_score(application_id, cibil_score)

        return update_result

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return False


def start_consumer():
    if not kafka_utils.KAFKA_ENABLED:
        logger.info("Kafka is disabled. Consumer not started.")
        return

    logger.info(
        f"Starting Kafka consumer for topic {kafka_utils.LOAN_APPLICATIONS_TOPIC}"
    )

    try:
        # Create consumer
        consumer = KafkaConsumer(
            kafka_utils.LOAN_APPLICATIONS_TOPIC,
            bootstrap_servers=kafka_utils.KAFKA_BOOTSTRAP_SERVERS,
            group_id=kafka_utils.KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
        )

        logger.info(
            f"Kafka consumer initialized successfully. Listening for messages on topic {kafka_utils.LOAN_APPLICATIONS_TOPIC}"
        )

        # Process messages
        for message in consumer:
            logger.info(
                f"Received message from partition {message.partition}, offset {message.offset}"
            )
            process_message(message)

    except NoBrokersAvailable:
        logger.error(
            f"No Kafka brokers available at {kafka_utils.KAFKA_BOOTSTRAP_SERVERS}"
        )
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}")


def start_consumer_thread():
    """
    Start the Kafka consumer in a separate thread
    """
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.daemon = True  # Thread will exit when main thread exits
    consumer_thread.start()
    logger.info("Kafka consumer thread started")
    return consumer_thread


if __name__ == "__main__":
    # This allows the script to be run directly for testing
    start_consumer()

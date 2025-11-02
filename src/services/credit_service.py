import json
import random

import src.core.config as config
from src.core.logging_config import logger
from src.kafka.kafka_producer import MessageProducer


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


def handle_application_event(message):
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

        MessageProducer.produce_message(
            config.LOAN_APPLICATIONS_TOPIC[1],
            application_id,
            {
                "application_id": application_id,
                "cibil_score": cibil_score,
                "application_data": application_data,
            },
        )

        return True

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return False

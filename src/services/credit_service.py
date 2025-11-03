"""
Credit service for CIBIL score calculation.
"""

import json
import random

import src.core.config as config
from src.core.constants import (
    CIBIL_BASE_SCORE,
    CIBIL_MAX_SCORE,
    CIBIL_MIN_SCORE,
    HIGH_INCOME_SCORE_BONUS,
    HIGH_INCOME_THRESHOLD_INR,
    HOME_LOAN_SCORE_BONUS,
    LOW_INCOME_SCORE_PENALTY,
    LOW_INCOME_THRESHOLD_INR,
    PERSONAL_LOAN_SCORE_PENALTY,
    SCORE_RANDOM_FACTOR_MAX,
    SCORE_RANDOM_FACTOR_MIN,
    TEST_PAN_HIGH_SCORE,
    TEST_PAN_HIGH_SCORE_VALUE,
    TEST_PAN_LOW_SCORE,
    TEST_PAN_LOW_SCORE_VALUE,
)
from src.core.logging_config import get_logger
from src.kafka.kafka_producer import MessageProducer

logger = get_logger(__name__)


class CreditScoreService:
    """
    Service for calculating CIBIL scores based on application data.
    """

    # Test PAN numbers with predefined scores (for testing only)
    TEST_PAN_SCORES = {
        TEST_PAN_HIGH_SCORE: TEST_PAN_HIGH_SCORE_VALUE,
        TEST_PAN_LOW_SCORE: TEST_PAN_LOW_SCORE_VALUE,
    }

    @staticmethod
    def calculate_cibil_score(application_data: dict) -> int:
        """
        Calculate CIBIL score based on application data.

        Score calculation logic:
        - Base score: 650
        - High income (>75k): +40
        - Low income (<30k): -20
        - Personal loan (unsecured): -10
        - Home loan (secured): +10
        - Random factor: -5 to +5
        - Final range: 300-900

        Args:
            application_data: Dictionary containing application details

        Returns:
            Calculated CIBIL score (300-900)
        """
        pan_number = application_data.get("pan_number")

        # Check if this is a test PAN number
        if pan_number in CreditScoreService.TEST_PAN_SCORES:
            test_score = CreditScoreService.TEST_PAN_SCORES[pan_number]
            logger.info(f"Using test score {test_score} for PAN {pan_number}")
            return test_score

        # Extract relevant data for calculation
        monthly_income = float(application_data.get("monthly_income_inr", 0))
        loan_type = application_data.get("loan_type", "").upper()

        # Start with base score
        score = CIBIL_BASE_SCORE
        adjustments = []

        # Adjust based on income
        if monthly_income > HIGH_INCOME_THRESHOLD_INR:
            score += HIGH_INCOME_SCORE_BONUS
            adjustments.append(f"high_income:+{HIGH_INCOME_SCORE_BONUS}")
        elif monthly_income < LOW_INCOME_THRESHOLD_INR:
            score -= LOW_INCOME_SCORE_PENALTY
            adjustments.append(f"low_income:-{LOW_INCOME_SCORE_PENALTY}")

        # Adjust based on loan type
        if loan_type == "PERSONAL":
            score -= PERSONAL_LOAN_SCORE_PENALTY
            adjustments.append(f"personal_loan:-{PERSONAL_LOAN_SCORE_PENALTY}")
        elif loan_type == "HOME":
            score += HOME_LOAN_SCORE_BONUS
            adjustments.append(f"home_loan:+{HOME_LOAN_SCORE_BONUS}")

        # Add small random factor for realism
        random_factor = random.randint(SCORE_RANDOM_FACTOR_MIN, SCORE_RANDOM_FACTOR_MAX)
        score += random_factor
        adjustments.append(f"random:{random_factor:+d}")

        # Ensure score is within valid range
        final_score = max(CIBIL_MIN_SCORE, min(CIBIL_MAX_SCORE, score))

        logger.info(
            f"CIBIL score calculation: base={CIBIL_BASE_SCORE}, "
            f"adjustments=[{', '.join(adjustments)}], final={final_score}"
        )

        return final_score


def handle_application_event(message) -> bool:
    """
    Handle Kafka message for new loan application event.
    Calculates CIBIL score and publishes to credit reports topic.

    Args:
        message: Kafka message containing application data

    Returns:
        True if processed successfully, False otherwise
    """
    try:
        # Parse message value
        application_data = json.loads(message.value)
        application_id = application_data.get("id")

        if not application_id:
            logger.error("Message does not contain application ID")
            return False

        logger.info(f"Processing application {application_id}")

        # Calculate CIBIL score
        cibil_score = CreditScoreService.calculate_cibil_score(application_data)
        logger.info(
            f"Calculated CIBIL score for application {application_id}: {cibil_score}"
        )

        # Publish message with application_id, cibil_score, and application_data
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
        logger.error(f"Error processing application message: {e}")
        return False

"""
Constants for loan prequalification service business logic.
"""

# CIBIL Score Calculation Constants
CIBIL_BASE_SCORE = 650
CIBIL_MIN_SCORE = 300
CIBIL_MAX_SCORE = 900

# Income thresholds for score adjustments
HIGH_INCOME_THRESHOLD_INR = 75000
LOW_INCOME_THRESHOLD_INR = 30000

# Score adjustments based on income
HIGH_INCOME_SCORE_BONUS = 40
LOW_INCOME_SCORE_PENALTY = 20

# Score adjustments based on loan type
PERSONAL_LOAN_SCORE_PENALTY = 10  # Unsecured loan
HOME_LOAN_SCORE_BONUS = 10  # Secured loan

# Random factor range for score variability
SCORE_RANDOM_FACTOR_MIN = -5
SCORE_RANDOM_FACTOR_MAX = 5

# Decision Making Constants
MIN_CIBIL_SCORE_FOR_APPROVAL = 650
LOAN_TERM_MONTHS = 48  # Used for EMI calculation (loan_amount / term)

# Kafka Configuration
KAFKA_PRODUCER_TIMEOUT_SECONDS = 5
KAFKA_AUTO_COMMIT_INTERVAL_MS = 5000

# Test PAN Numbers (for testing purposes only)
TEST_PAN_HIGH_SCORE = "ABCDE1234F"
TEST_PAN_HIGH_SCORE_VALUE = 790
TEST_PAN_LOW_SCORE = "FGHIJ5678K"
TEST_PAN_LOW_SCORE_VALUE = 610

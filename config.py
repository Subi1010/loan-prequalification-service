import os

KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
LOAN_APPLICATIONS_TOPIC = ['loan_applications_submitted','credit_reports_generated']
KAFKA_ENABLED = os.environ.get('KAFKA_ENABLED', 'true').lower() == 'true'
KAFKA_GROUP_ID = 'loan_application_processor'

# Use DATABASE_URL from environment if available, otherwise use local database
SQLALCHEMY_DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:test1234@localhost:5432/LoanAppDatabase'
)

import os

KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
LOAN_APPLICATIONS_TOPIC = 'loan_applications_submitted'
KAFKA_ENABLED = os.environ.get('KAFKA_ENABLED', 'true').lower() == 'true'
KAFKA_GROUP_ID = 'loan_application_processor'

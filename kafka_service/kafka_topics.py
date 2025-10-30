import logging
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import kafka_service.kafka_utils as kafka_utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_kafka_topic():

    #Create the Kafka topic for loan applications if it doesn't exist
    if not kafka_utils.KAFKA_ENABLED:
        logger.info("Kafka is disabled. Topic creation skipped.")
        return False

    try:
        admin_client = KafkaAdminClient(bootstrap_servers=kafka_utils.KAFKA_BOOTSTRAP_SERVERS)

        topic = NewTopic(
            name=kafka_utils.LOAN_APPLICATIONS_TOPIC,
            num_partitions=1,
            replication_factor=1
        )

        admin_client.create_topics([topic])
        logger.info(f"Topic '{kafka_utils.LOAN_APPLICATIONS_TOPIC}' created successfully")
        return True
    except TopicAlreadyExistsError:
        logger.info(f"Topic '{kafka_utils.LOAN_APPLICATIONS_TOPIC}' already exists")
        return True
    except NoBrokersAvailable:
        logger.warning(f"No Kafka brokers available at {kafka_utils.KAFKA_BOOTSTRAP_SERVERS}. Topic creation skipped.")
        return False
    except Exception as e:
        logger.error(f"Failed to create topic '{kafka_utils.LOAN_APPLICATIONS_TOPIC}': {e}")
        return False
    finally:
        if 'admin_client' in locals():
            admin_client.close()


create_kafka_topic()

import src.core.config as config
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
from src.core.logging_config import get_logger

logger = get_logger(__name__)


def create_kafka_topic():
    """
    Create Kafka topics for loan applications if they don't exist.

    Returns:
        bool: True if all topics were created or already exist, False otherwise
    """
    if not config.KAFKA_ENABLED:
        logger.info("Kafka is disabled. Topic creation skipped.")
        return False

    admin_client = None

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS
        )

        for topic in config.LOAN_APPLICATIONS_TOPIC:
            try:
                topic_create = NewTopic(
                    name=topic,
                    num_partitions=1,
                    replication_factor=1,
                )

                admin_client.create_topics([topic_create])
                logger.info(f"Topic '{topic}' created successfully")
            except TopicAlreadyExistsError:
                logger.info(f"Topic '{topic}' already exists")

        return True

    except NoBrokersAvailable:
        logger.warning(
            f"No Kafka brokers available at {config.KAFKA_BOOTSTRAP_SERVERS}. Topic creation skipped."
        )
        return False
    except Exception as e:
        logger.error(f"Failed to create topics: {e}")
        return False
    finally:
        if admin_client is not None:
            admin_client.close()

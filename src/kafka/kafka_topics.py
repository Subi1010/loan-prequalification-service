import logging

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError

import src.core.config as config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_kafka_topic():
    # Create the Kafka topic for loan applications if it doesn't exist
    if not config.KAFKA_ENABLED:
        logger.info("Kafka is disabled. Topic creation skipped.")
        return False

    success = True
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
                logger.info(
                  f"Topic '{config.LOAN_APPLICATIONS_TOPIC}' created successfully"
                  )
                return True
            except TopicAlreadyExistsError:
                logger.info(f"Topic '{topic}' already exists")
                return True

    except NoBrokersAvailable:
        logger.warning(
            f"No Kafka brokers available at {config.KAFKA_BOOTSTRAP_SERVERS}. Topic creation skipped."
        )
        return False
    except Exception as e:
        logger.error(
            f"Failed to create topic '{kafka_utils.LOAN_APPLICATIONS_TOPIC}': {e}"
        )
        return False
    finally:
        if "admin_client" in locals():
            admin_client.close()


create_kafka_topic()

import json
import logging
import os
import config as config
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import config as config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logger.info(f"Kafka configuration: bootstrap_servers={config.KAFKA_BOOTSTRAP_SERVERS}, topic={config.LOAN_APPLICATIONS_TOPIC}, enabled={config.KAFKA_ENABLED}")

# Initialize Kafka producer
producer = None
if config.KAFKA_ENABLED:
    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: str(k).encode("utf-8") if k else None,
        )
        logger.info("Kafka producer initialized successfully")
    except NoBrokersAvailable:
        logger.warning(
            f"No Kafka brokers available at {config.KAFKA_BOOTSTRAP_SERVERS}. Messages will not be sent to Kafka."
        )
    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")
else:
    logger.info("Kafka is disabled. Messages will not be sent to Kafka.")


def send_data_to_kafka(application_id, application_data,topic):
    if not config.KAFKA_ENABLED:
        logger.info(
            f"Kafka is disabled. Application {application_id} not sent to Kafka."
        )
        return False

    if producer is None:
        logger.warning(
            f"Kafka producer not initialized. Application {application_id} not sent to Kafka."
        )
        return False

    try:
        future = producer.send(
            topic,
            key=application_id,
            value=application_data,
        )

        # TO-DO : make it Asynchronous and add the retry for sending messages.

        # Block until message is sent (or timeout after 5 seconds)
        record_metadata = future.get(timeout=5)

        logger.info(
            f"Application sent to Kafka topic '{topic}' "
            f"[partition: {record_metadata.partition}, offset: {record_metadata.offset}]"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send application to Kafka: {e}")
        return False

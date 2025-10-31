import json

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from src.core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_ENABLED
from src.core.logging_config import logger


class MessageProducer:
    producer = None

    @staticmethod
    def initialize_producer():
        logger.info(
            f"Kafka configuration: bootstrap_servers={KAFKA_BOOTSTRAP_SERVERS}, enabled={KAFKA_ENABLED}"
        )

        if KAFKA_ENABLED:
            try:
                MessageProducer.producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    key_serializer=lambda k: str(k).encode("utf-8") if k else None,
                )
                logger.info("Kafka producer initialized successfully")
            except NoBrokersAvailable:
                logger.warning(
                    f"No Kafka brokers available at {KAFKA_BOOTSTRAP_SERVERS}. Messages will not be sent to Kafka."
                )
            except Exception as e:
                logger.error(f"Failed to initialize Kafka producer: {e}")
        else:
            logger.info("Kafka is disabled. Messages will not be sent to Kafka.")

    @staticmethod
    def produce_message(topic, key, value):
        if not KAFKA_ENABLED:
            logger.info(f"Kafka is disabled. Application {key} not sent to Kafka.")
            return False

        if MessageProducer.producer is None:
            logger.warning(
                f"Kafka producer not initialized. Application {key} not sent to Kafka."
            )
            return False

        try:
            future = MessageProducer.producer.send(
                topic,
                key=key,
                value=value,
            )
            # TO-DO : make it Asynchronous and add the retry for sending messages.

            # Block until message is sent (or timeout after 5 seconds)
            record_metadata = future.get(timeout=5)

            logger.info(
                f"Message sent to Kafka topic '{topic}' "
                f"[partition: {record_metadata.partition}, offset: {record_metadata.offset}]"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send application to Kafka: {e}")
            return False

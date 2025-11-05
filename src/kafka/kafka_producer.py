"""
Kafka producer for publishing messages to Kafka topics.
"""

import json
from typing import Any

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from src.core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_ENABLED
from src.core.constants import KAFKA_PRODUCER_TIMEOUT_SECONDS
from src.core.logging_config import get_logger


class MessageProducer:
    """
    Kafka message producer using singleton pattern.

    Handles initialization and message publishing to Kafka topics.
    """

    producer: KafkaProducer | None = None
    logger = get_logger(__name__)

    @staticmethod
    def initialize_producer() -> None:
        """
        Initialize the Kafka producer with configuration.

        Creates a singleton KafkaProducer instance with JSON serialization.
        Handles cases where Kafka is disabled or brokers are unavailable.
        """
        MessageProducer.logger.info(
            f"Kafka configuration: bootstrap_servers={KAFKA_BOOTSTRAP_SERVERS}, enabled={KAFKA_ENABLED}"
        )

        if not KAFKA_ENABLED:
            MessageProducer.logger.info(
                "Kafka is disabled. Messages will not be sent to Kafka."
            )
            return

        try:
            MessageProducer.producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: str(k).encode("utf-8") if k else None,
                # Add retry configuration
                retries=3,
                retry_backoff_ms=100,
                # Add compression
                compression_type="gzip",
            )
            MessageProducer.logger.info("Kafka producer initialized successfully")
        except NoBrokersAvailable:
            MessageProducer.logger.warning(
                f"No Kafka brokers available at {KAFKA_BOOTSTRAP_SERVERS}. "
                "Messages will not be sent to Kafka."
            )
        except Exception as e:
            MessageProducer.logger.error(f"Failed to initialize Kafka producer: {e}")

    @staticmethod
    def produce_message(topic: str, key: str, value: dict[str, Any]) -> bool:
        """
        Publish a message to a Kafka topic.

        Args:
            topic: Kafka topic name
            key: Message key (typically application ID)
            value: Message value (dictionary to be JSON serialized)

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not KAFKA_ENABLED:
            MessageProducer.logger.info(
                f"Kafka is disabled. Message with key {key} not sent to Kafka."
            )
            return False

        if MessageProducer.producer is None:
            MessageProducer.logger.warning(
                f"Kafka producer not initialized. Message with key {key} not sent to Kafka."
            )
            return False

        try:
            future = MessageProducer.producer.send(
                topic,
                key=key,
                value=value,
            )

            # Block until message is sent (synchronous for now)
            record_metadata = future.get(timeout=KAFKA_PRODUCER_TIMEOUT_SECONDS)

            MessageProducer.logger.info(
                f"Message sent to Kafka topic '{topic}' "
                f"[partition: {record_metadata.partition}, offset: {record_metadata.offset}]"
            )
            return True

        except Exception as e:
            MessageProducer.logger.error(
                f"Failed to send message to Kafka topic '{topic}': {e}"
            )
            return False

    @staticmethod
    def close_producer() -> None:
        """
        Close the Kafka producer and release resources.

        Should be called during application shutdown.
        """
        if MessageProducer.producer is not None:
            try:
                MessageProducer.producer.close()
                MessageProducer.logger.info("Kafka producer closed successfully")
            except Exception as e:
                MessageProducer.logger.error(f"Error closing Kafka producer: {e}")

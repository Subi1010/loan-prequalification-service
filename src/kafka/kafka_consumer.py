"""
Kafka consumer for processing messages from Kafka topics.
"""

import threading

import src.core.config as config
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from src.core.constants import KAFKA_AUTO_COMMIT_INTERVAL_MS
from src.core.logging_config import get_logger
from src.services.app_processor import TOPIC_HANDLERS


class MessageConsumer:
    """
    Kafka message consumer using background thread processing.

    Listens to configured topics and dispatches messages to appropriate handlers.
    """

    logger = get_logger(__name__)

    @staticmethod
    def initialize_consumer() -> None:
        """
        Initialize and run the Kafka consumer.

        Creates a KafkaConsumer instance and processes messages in an infinite loop.
        Messages are dispatched to handlers based on topic name.

        This method blocks indefinitely and should be run in a separate thread.
        """
        if not config.KAFKA_ENABLED:
            MessageConsumer.logger.info("Kafka is disabled. Consumer not started.")
            return

        MessageConsumer.logger.info(
            f"Starting Kafka consumer for topics {config.LOAN_APPLICATIONS_TOPIC}"
        )

        try:
            # Create consumer
            consumer = KafkaConsumer(
                *config.LOAN_APPLICATIONS_TOPIC,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.KAFKA_GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                auto_commit_interval_ms=KAFKA_AUTO_COMMIT_INTERVAL_MS,
                # Add JSON deserialization at consumer level
                value_deserializer=lambda m: m.decode("utf-8"),
            )

            MessageConsumer.logger.info(
                f"Kafka consumer initialized successfully. "
                f"Listening for messages on topics {config.LOAN_APPLICATIONS_TOPIC}"
            )

            # Process messages in infinite loop
            for message in consumer:
                MessageConsumer.logger.info(
                    f"Received message from topic '{message.topic}', "
                    f"partition {message.partition}, offset {message.offset}"
                )

                # Get handler for this topic
                handler = TOPIC_HANDLERS.get(message.topic)

                if handler:
                    try:
                        success = handler(message)
                        if success:
                            MessageConsumer.logger.debug(
                                f"Successfully processed message from topic '{message.topic}'"
                            )
                        else:
                            MessageConsumer.logger.warning(
                                f"Handler returned False for message from topic '{message.topic}'"
                            )
                    except Exception as e:
                        MessageConsumer.logger.error(
                            f"Error in handler for topic '{message.topic}': {e}"
                        )
                else:
                    MessageConsumer.logger.warning(
                        f"No handler defined for topic '{message.topic}'. Message skipped."
                    )

        except NoBrokersAvailable:
            MessageConsumer.logger.error(
                f"No Kafka brokers available at {config.KAFKA_BOOTSTRAP_SERVERS}"
            )
        except Exception as e:
            MessageConsumer.logger.error(f"Error in Kafka consumer: {e}")

    @staticmethod
    def initialize_consumer_thread() -> threading.Thread:
        """
        Start the Kafka consumer in a separate daemon thread.

        The consumer thread will automatically exit when the main application exits.

        Returns:
            Thread object for the consumer thread
        """
        consumer_thread = threading.Thread(
            target=MessageConsumer.initialize_consumer, name="KafkaConsumerThread"
        )
        consumer_thread.daemon = True  # Thread will exit when main thread exits
        consumer_thread.start()
        MessageConsumer.logger.info("Kafka consumer thread started")
        return consumer_thread


if __name__ == "__main__":
    # This allows the script to be run directly for testing
    MessageConsumer.initialize_consumer()

from unittest.mock import MagicMock, patch

from kafka.errors import NoBrokersAvailable
from src.kafka.kafka_consumer import MessageConsumer


class TestKafkaConsumer:
    def test_initialize_consumer_kafka_disabled(self):
        # Mock the KafkaConsumer class and config values
        with (
            patch("src.kafka.kafka_consumer.KafkaConsumer") as mock_kafka_consumer,
            patch("src.kafka.kafka_consumer.config.KAFKA_ENABLED", False),
        ):
            # Call the method
            MessageConsumer.initialize_consumer()

            # Verify the consumer was not initialized
            mock_kafka_consumer.assert_not_called()

    def test_initialize_consumer_no_brokers(self):
        # Mock the KafkaConsumer class to raise NoBrokersAvailable and config values
        with (
            patch(
                "src.kafka.kafka_consumer.KafkaConsumer",
                side_effect=NoBrokersAvailable(),
            ),
            patch("src.kafka.kafka_consumer.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_consumer.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_consumer.config.LOAN_APPLICATIONS_TOPIC",
                ["test_topic"],
            ),
        ):
            # Call the method
            MessageConsumer.initialize_consumer()

            # No assertion needed, just verifying it doesn't raise an exception

    def test_initialize_consumer_success(self):
        # Create a mock message
        mock_message = MagicMock()
        mock_message.topic = "loan_applications_submitted"
        mock_message.partition = 0
        mock_message.offset = 123

        # Create a mock consumer that yields one message then raises StopIteration
        mock_consumer = MagicMock()
        mock_consumer.__iter__.return_value = iter([mock_message])

        # Mock the KafkaConsumer class to return our mock consumer and config values
        mock_handler = MagicMock()
        with (
            patch("src.kafka.kafka_consumer.KafkaConsumer", return_value=mock_consumer),
            patch("src.kafka.kafka_consumer.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_consumer.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_consumer.config.LOAN_APPLICATIONS_TOPIC",
                ["loan_applications_submitted"],
            ),
            patch(
                "src.kafka.kafka_consumer.TOPIC_HANDLERS",
                {"loan_applications_submitted": mock_handler},
            ),
        ):
            # Call the method
            MessageConsumer.initialize_consumer()

            # Verify the handler was called with the message
            mock_handler.assert_called_once_with(mock_message)

    def test_initialize_consumer_unknown_topic(self):
        # Create a mock message with an unknown topic
        mock_message = MagicMock()
        mock_message.topic = "unknown_topic"
        mock_message.partition = 0
        mock_message.offset = 123

        # Create a mock consumer that yields one message then raises StopIteration
        mock_consumer = MagicMock()
        mock_consumer.__iter__.return_value = iter([mock_message])

        # Mock the KafkaConsumer class to return our mock consumer and config values
        with (
            patch("src.kafka.kafka_consumer.KafkaConsumer", return_value=mock_consumer),
            patch("src.kafka.kafka_consumer.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_consumer.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_consumer.config.LOAN_APPLICATIONS_TOPIC",
                ["loan_applications_submitted"],
            ),
            patch("src.kafka.kafka_consumer.TOPIC_HANDLERS", {}),
        ):
            # Call the method
            MessageConsumer.initialize_consumer()

            # No assertion needed, just verifying it doesn't raise an exception

    def test_initialize_consumer_exception(self):
        # Mock the KafkaConsumer class to raise a general exception and config values
        with (
            patch(
                "src.kafka.kafka_consumer.KafkaConsumer",
                side_effect=Exception("Test exception"),
            ),
            patch("src.kafka.kafka_consumer.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_consumer.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_consumer.config.LOAN_APPLICATIONS_TOPIC",
                ["test_topic"],
            ),
        ):
            # Call the method
            MessageConsumer.initialize_consumer()

            # No assertion needed, just verifying it doesn't raise an exception

    def test_initialize_consumer_thread(self):
        # Mock the initialize_consumer method and threading.Thread class
        with (
            patch.object(MessageConsumer, "initialize_consumer"),
            patch("src.kafka.kafka_consumer.threading.Thread") as mock_thread,
        ):
            # Call the method
            thread = MessageConsumer.initialize_consumer_thread()

            # Verify the thread was created and started
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()

            # Verify the thread is a daemon thread
            args, kwargs = mock_thread.call_args
            assert kwargs["target"] == MessageConsumer.initialize_consumer
            assert thread.daemon is True

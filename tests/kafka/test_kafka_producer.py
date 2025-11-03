from unittest.mock import MagicMock, patch

from kafka.errors import NoBrokersAvailable
from src.kafka.kafka_producer import MessageProducer


class TestKafkaProducer:
    def test_initialize_producer_success(self):
        # Mock the KafkaProducer class and config values
        with (
            patch("src.kafka.kafka_producer.KafkaProducer") as mock_kafka_producer,
            patch("src.kafka.kafka_producer.KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            patch("src.kafka.kafka_producer.KAFKA_ENABLED", True),
        ):
            # Call the method
            MessageProducer.producer = None  # Reset the producer
            MessageProducer.initialize_producer()

            # Verify the producer was initialized
            mock_kafka_producer.assert_called_once()
            assert MessageProducer.producer is not None

    def test_initialize_producer_kafka_disabled(self):
        # Mock the KafkaProducer class and config values
        with (
            patch("src.kafka.kafka_producer.KafkaProducer") as mock_kafka_producer,
            patch("src.kafka.kafka_producer.KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            patch("src.kafka.kafka_producer.KAFKA_ENABLED", False),
        ):
            # Call the method
            MessageProducer.producer = None  # Reset the producer
            MessageProducer.initialize_producer()

            # Verify the producer was not initialized
            mock_kafka_producer.assert_not_called()
            assert MessageProducer.producer is None

    def test_initialize_producer_no_brokers(self):
        # Mock the KafkaProducer class to raise NoBrokersAvailable and config values
        with (
            patch(
                "src.kafka.kafka_producer.KafkaProducer",
                side_effect=NoBrokersAvailable(),
            ),
            patch("src.kafka.kafka_producer.KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            patch("src.kafka.kafka_producer.KAFKA_ENABLED", True),
        ):
            # Call the method
            MessageProducer.producer = None  # Reset the producer
            MessageProducer.initialize_producer()

            # Verify the producer was not initialized
            assert MessageProducer.producer is None

    def test_produce_message_success(self):
        # Create a mock producer
        mock_producer = MagicMock()
        mock_future = MagicMock()
        mock_producer.send.return_value = mock_future

        # Mock the producer and config
        with (
            patch.object(MessageProducer, "producer", mock_producer),
            patch("src.kafka.kafka_producer.KAFKA_ENABLED", True),
        ):
            # Call the method
            result = MessageProducer.produce_message(
                "test_topic", "test_key", {"data": "test_value"}
            )

            # Verify the message was sent
            mock_producer.send.assert_called_once_with(
                "test_topic",
                key="test_key",
                value={"data": "test_value"},
            )
            mock_future.get.assert_called_once()
            assert result is True

    def test_produce_message_kafka_disabled(self):
        # Create a mock producer
        mock_producer = MagicMock()

        # Mock the producer and config
        with (
            patch.object(MessageProducer, "producer", mock_producer),
            patch("src.kafka.kafka_producer.KAFKA_ENABLED", False),
        ):
            # Call the method
            result = MessageProducer.produce_message(
                "test_topic", "test_key", {"data": "test_value"}
            )

            # Verify the message was not sent
            mock_producer.send.assert_not_called()
            assert result is False

    def test_produce_message_producer_not_initialized(self):
        # Mock the config
        with patch("src.kafka.kafka_producer.KAFKA_ENABLED", True):
            # Call the method with no producer
            MessageProducer.producer = None
            result = MessageProducer.produce_message(
                "test_topic", "test_key", {"data": "test_value"}
            )

            # Verify the result
            assert result is False

    def test_produce_message_exception(self):
        # Create a mock producer that raises an exception
        mock_producer = MagicMock()
        mock_producer.send.side_effect = Exception("Test exception")

        # Mock the producer and config
        with (
            patch.object(MessageProducer, "producer", mock_producer),
            patch("src.kafka.kafka_producer.KAFKA_ENABLED", True),
        ):
            # Call the method
            result = MessageProducer.produce_message(
                "test_topic", "test_key", {"data": "test_value"}
            )

            # Verify the result
            assert result is False

from unittest.mock import MagicMock, patch

from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
from src.kafka.kafka_topics import create_kafka_topic


class TestKafkaTopics:
    def test_create_kafka_topic_success(self):
        # Mock the KafkaAdminClient
        mock_admin_client = MagicMock()

        # Mock the config values and KafkaAdminClient constructor
        with (
            patch("src.kafka.kafka_topics.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_topics.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_topics.config.LOAN_APPLICATIONS_TOPIC",
                ["test_topic"],
            ),
            patch(
                "src.kafka.kafka_topics.KafkaAdminClient",
                return_value=mock_admin_client,
            ),
        ):
            # Call the function
            result = create_kafka_topic()

            # Verify the topics were created
            assert mock_admin_client.create_topics.call_count == 1
            assert result is True

            # Verify the admin client was closed
            mock_admin_client.close.assert_called_once()

    def test_create_kafka_topic_already_exists(self):
        # Mock the KafkaAdminClient
        mock_admin_client = MagicMock()
        mock_admin_client.create_topics.side_effect = TopicAlreadyExistsError()

        # Mock the config values and KafkaAdminClient constructor
        with (
            patch("src.kafka.kafka_topics.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_topics.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_topics.config.LOAN_APPLICATIONS_TOPIC",
                ["test_topic"],
            ),
            patch(
                "src.kafka.kafka_topics.KafkaAdminClient",
                return_value=mock_admin_client,
            ),
        ):
            # Call the function
            result = create_kafka_topic()

            # Verify the result
            assert result is True

            # Verify the admin client was closed
            mock_admin_client.close.assert_called_once()

    def test_create_kafka_topic_kafka_disabled(self):
        # Mock the KafkaAdminClient
        mock_admin_client = MagicMock()

        # Mock the config values and KafkaAdminClient constructor
        with (
            patch("src.kafka.kafka_topics.config.KAFKA_ENABLED", False),
            patch(
                "src.kafka.kafka_topics.KafkaAdminClient",
                return_value=mock_admin_client,
            ),
        ):
            # Call the function
            result = create_kafka_topic()

            # Verify the admin client was not created
            assert not mock_admin_client.create_topics.called
            assert result is False

    def test_create_kafka_topic_no_brokers(self):
        # Mock the KafkaAdminClient constructor to raise NoBrokersAvailable and config values
        with (
            patch(
                "src.kafka.kafka_topics.KafkaAdminClient",
                side_effect=NoBrokersAvailable(),
            ),
            patch("src.kafka.kafka_topics.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_topics.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch("src.kafka.kafka_topics.locals", return_value={}),
        ):
            # Call the function
            result = create_kafka_topic()

            # Verify the result
            assert result is False

    def test_create_kafka_topic_exception(self):
        # Mock the KafkaAdminClient
        mock_admin_client = MagicMock()
        mock_admin_client.create_topics.side_effect = Exception("Test exception")

        # Mock the config values and KafkaAdminClient constructor
        with (
            patch("src.kafka.kafka_topics.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_topics.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_topics.config.LOAN_APPLICATIONS_TOPIC",
                ["test_topic"],
            ),
            patch(
                "src.kafka.kafka_topics.KafkaAdminClient",
                return_value=mock_admin_client,
            ),
        ):
            # Call the function
            result = create_kafka_topic()

            # Verify the result
            assert result is False

            # Verify the admin client was closed
            mock_admin_client.close.assert_called_once()

    def test_create_kafka_topic_multiple_topics(self):
        # Mock the KafkaAdminClient
        mock_admin_client = MagicMock()

        # Mock the config values with multiple topics and KafkaAdminClient constructor
        with (
            patch("src.kafka.kafka_topics.config.KAFKA_ENABLED", True),
            patch(
                "src.kafka.kafka_topics.config.KAFKA_BOOTSTRAP_SERVERS",
                "localhost:9092",
            ),
            patch(
                "src.kafka.kafka_topics.config.LOAN_APPLICATIONS_TOPIC",
                ["topic1", "topic2"],
            ),
            patch(
                "src.kafka.kafka_topics.KafkaAdminClient",
                return_value=mock_admin_client,
            ),
        ):
            # Call the function
            result = create_kafka_topic()

            # Verify the topics were created
            assert mock_admin_client.create_topics.call_count == 2
            assert result is True

            # Verify the admin client was closed
            mock_admin_client.close.assert_called_once()

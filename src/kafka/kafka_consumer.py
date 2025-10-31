import threading

import src.core.config as config
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from src.core.logging_config import logger
from src.services.app_processor import TOPIC_HANDLERS

class MessageConsumer:

  @staticmethod
  def initialize_consumer():

      if not config.KAFKA_ENABLED:
          logger.info("Kafka is disabled. Consumer not started.")
          return

      logger.info(f"Starting Kafka consumer for topic {config.LOAN_APPLICATIONS_TOPIC}")

      try:
          # Create consumer
          consumer = KafkaConsumer(
              *config.LOAN_APPLICATIONS_TOPIC,
              bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
              group_id=config.KAFKA_GROUP_ID,
              auto_offset_reset="earliest",
              enable_auto_commit=True,
              auto_commit_interval_ms=5000,
          )

          logger.info(f"Kafka consumer initialized successfully. Listening for messages on topic {config.LOAN_APPLICATIONS_TOPIC}")

          # Process messages
          for message in consumer:
              logger.info(
                  f"Received message from partition {message.partition}, offset {message.offset}"
              )
              handler = TOPIC_HANDLERS.get(message.topic)
              if handler:
                  handler(message)
              else:
                  logger.warning(
                      f"No handler defined for topic {message.topic}. Message skipped."
                  )

      except NoBrokersAvailable:
          logger.error(f"No Kafka brokers available at {config.KAFKA_BOOTSTRAP_SERVERS}")
      except Exception as e:
          logger.error(f"Error in Kafka consumer: {e}")

  @staticmethod
  def initialize_consumer_thread():
      """
      Start the Kafka consumer in a separate thread
      """
      consumer_thread = threading.Thread(target=MessageConsumer.initialize_consumer)
      consumer_thread.daemon = True  # Thread will exit when main thread exits
      consumer_thread.start()
      logger.info("Kafka consumer thread started")
      return consumer_thread


if __name__ == "__main__":
  # This allows the script to be run directly for testing
  MessageConsumer.initialize_consumer()

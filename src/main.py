"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

import src.models as models
from src.api import endpoints
from src.core.config import settings
from src.core.database import engine
from src.core.logging_config import get_logger
from src.kafka.kafka_consumer import MessageConsumer
from src.kafka.kafka_producer import MessageProducer
from src.kafka.kafka_topics import create_kafka_topic

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.

    Handles:
    - Database table creation
    - Kafka topic creation
    - Kafka producer initialization
    - Kafka consumer thread startup
    """
    logger.info("Application startup initiated")

    logger.info("Creating database tables")
    models.Base.metadata.create_all(bind=engine)

    logger.info("Creating Kafka topics")
    create_kafka_topic()

    logger.info("Initializing Kafka producer")
    MessageProducer.initialize_producer()

    logger.info("Starting Kafka consumer thread")
    MessageConsumer.initialize_consumer_thread()

    logger.info("Application startup completed")

    yield

    logger.info("Application shutdown initiated")
    MessageProducer.close_producer()
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A loan prequalification service that processes applications asynchronously using Kafka",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(endpoints.router)

import logging

from fastapi import FastAPI

import src.kafka.kafka_consumer as kafka_consumer  # Import for CIBIL score calculation consumer
import src.models as models
from src.database import engine
from src.api import application
import src.kafka.kafka_producer as kafka_producer
import src.kafka.kafka_consumer as kafka_consumer
import logging
import src.kafka.kafka_topics as kafka_topics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(application.router)


# Start Kafka consumer in a separate thread
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Kafka consumer thread")
    kafka_consumer.start_consumer_thread()
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")

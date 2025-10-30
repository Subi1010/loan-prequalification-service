from fastapi import FastAPI
import models
from database import engine
from routers import application
import kafka_service.kafka_producer as kafka_producer  # Import to ensure Kafka topic is created on startup
import kafka_service.kafka_consumer as kafka_consumer  # Import for CIBIL score calculation consumer
import logging
import kafka_service.kafka_topics as kafka_topics

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

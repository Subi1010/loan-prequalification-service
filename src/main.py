from contextlib import asynccontextmanager

from fastapi import FastAPI

import src.kafka.kafka_consumer as kafka_consumer
import src.models as models
from src.api import application
from src.core.logging_config import logger
from src.database import engine
from src.kafka.kafka_producer import MessageProducer


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    models.Base.metadata.create_all(bind=engine)
    MessageProducer.initialize_producer()
    logger.info("Starting Kafka consumer thread")
    kafka_consumer.start_consumer_thread()

    yield

    print("Shutting down...")


app = FastAPI(lifespan=lifespan)
app.include_router(application.router)

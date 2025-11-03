from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.database import Base, get_db
from src.kafka.kafka_producer import MessageProducer
from src.main import app

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    # Create the database tables
    Base.metadata.create_all(bind=engine)

    # Create a db session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Create a test client using the FastAPI app
    with TestClient(app) as test_client:
        yield test_client

    # Reset the dependency override after the test
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def mock_kafka_producer():
    # Create a mock for the Kafka producer
    with patch.object(MessageProducer, "produce_message", return_value=True) as mock:
        yield mock

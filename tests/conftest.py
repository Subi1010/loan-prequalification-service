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


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create tables once for the entire test session"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a new database session with a rollback at the end of each test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Patch engine and Kafka operations in lifespan
    with (
        patch("src.main.engine", engine),
        patch("src.main.create_kafka_topic"),
        patch("src.main.MessageProducer.initialize_producer"),
        patch("src.main.MessageConsumer.initialize_consumer_thread"),
        patch("src.main.MessageProducer.close_producer"),
        TestClient(app) as test_client,
    ):
        yield test_client

    # Reset the dependency override after the test
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def mock_kafka_producer():
    # Create a mock for the Kafka producer
    with patch.object(MessageProducer, "produce_message", return_value=True) as mock:
        yield mock

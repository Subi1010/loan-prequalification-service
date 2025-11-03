# Tests for Loan Prequalification Service

This directory contains tests for the Loan Prequalification Service application.

## Structure

- `conftest.py`: Contains pytest fixtures used across multiple test files
- `api/`: Tests for API endpoints
  - `test_application.py`: Tests for application endpoints in `src/api/application.py`
- `core/`: Tests for core functionality (to be implemented)
- `services/`: Tests for service modules (to be implemented)
- `kafka/`: Tests for Kafka integration (to be implemented)

## Running Tests

To run all tests:

```bash
pytest
```

To run tests with coverage report:

```bash
pytest --cov=src
```

To run a specific test file:

```bash
pytest tests/api/test_application.py
```

To run a specific test:

```bash
pytest tests/api/test_application.py::TestApplicationEndpoints::test_create_application_success
```

## Test Database

Tests use an in-memory SQLite database instead of the PostgreSQL database used in production. This is configured in `conftest.py`.

## Mocking

- Kafka producer is mocked to avoid actual message production during tests
- Database sessions are created and torn down for each test to ensure isolation

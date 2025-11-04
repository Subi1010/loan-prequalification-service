# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based loan prequalification service that handles loan applications with PostgreSQL as the database backend and Kafka for asynchronous message processing. The service provides REST APIs for creating loan applications and checking their status, with CIBIL score calculation handled asynchronously via Kafka consumers.

## Running the Application

### Local Development
Start the development server locally:
```bash
uvicorn main:app --reload
```

### Docker Compose (Recommended)
Run the entire stack (app, PostgreSQL, Kafka, Zookeeper):
```bash
docker-compose up --build
```

To run in detached mode:
```bash
docker-compose up -d --build
```

Stop all services:
```bash
docker-compose down
```

The API will be available at http://localhost:8000. FastAPI automatically generates interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database Setup

The application connects to PostgreSQL with the following configuration:
- Database: `LoanAppDatabase`
- Host: `localhost:5432` (or `postgres:5432` in Docker)
- User: `postgres`
- Password: `test1234`

Database connection uses environment variable `DATABASE_URL` (see `database.py:9`), falling back to localhost if not set. Database tables are automatically created on application startup via SQLAlchemy's `create_all()` in `main.py:16`.

## Architecture

### Application Structure

- **main.py**: FastAPI application entry point, includes routers, initializes database tables, starts Kafka consumer thread
- **database.py**: Database connection setup with SQLAlchemy engine, session management, and dependency injection
- **models.py**: SQLAlchemy ORM model for the `applications` table
- **app_status.py**: Enum defining possible application statuses (`PENDING`, `PRE_APPROVED`, `REJECTED`, `MANUAL_REVIEW`)
- **routers/application.py**: API endpoints for loan application operations, publishes messages to Kafka
- **kafka_service/**: Kafka integration modules
  - **kafka_utils.py**: Configuration constants (bootstrap servers, topic names, group IDs)
  - **kafka_topics.py**: Topic creation and management
  - **kafka_producer.py**: Publishes loan application messages to Kafka
  - **kafka_consumer.py**: Consumes messages, calculates CIBIL scores, updates database

### Event-Driven Flow

1. **Application Creation** (`routers/application.py:32`):
   - POST request creates application in database with status "pending"
   - Application data published to Kafka topic `loan_applications_submitted`
   - Returns 202 Accepted immediately (asynchronous processing)

2. **CIBIL Score Processing** (`kafka_service/kafka_consumer.py:124`):
   - Consumer listens to `loan_applications_submitted` topic
   - Calculates CIBIL score based on income, loan type, and PAN number
   - Updates application record with calculated score
   - Runs in separate daemon thread started at application startup

3. **Status Checking** (`routers/application.py:64`):
   - GET request retrieves current application status and ID
   - CIBIL score populated after Kafka processing completes

### Kafka Configuration

Kafka is controlled via environment variables (see `kafka_service/kafka_utils.py`):
- `KAFKA_BOOTSTRAP_SERVERS`: Default `localhost:9092` (or `kafka:9093` in Docker)
- `KAFKA_ENABLED`: Set to `"false"` to disable Kafka functionality
- Topic: `loan_applications_submitted`
- Consumer Group: `loan_application_processor`

When Kafka is disabled or unavailable, the application continues to function but CIBIL scores will not be calculated.

### CIBIL Score Calculation Logic

The CIBIL score calculation (`kafka_service/kafka_consumer.py:19`) uses:
- Base score of 650
- Income adjustments: +40 for income > 75k, -20 for income < 30k
- Loan type adjustments: -10 for PERSONAL (unsecured), +10 for HOME (secured)
- Small random factor (-5 to +5) for realism
- Hardcoded scores for specific test PANs (ABCDE1234F → 790, FGHIJ5678K → 610)
- Final score clamped between 300-900

### Data Model

The `Applications` model uses:
- **UUID** as primary key (auto-generated)
- **DECIMAL** type for monetary values (monthly_income_inr, loan_amount_inr)
- **DateTime** fields with automatic UTC timestamps for created_at and updated_at
- **ApplicationStatus enum** for the status field with default value "pending"
- **Integer** for cibil_score (nullable, populated by consumer)

Key fields: id (UUID), pan_number, applicant_name, monthly_income_inr, loan_amount_inr, loan_type, status, cibil_score, created_at, updated_at

### API Endpoints

All endpoints are under the `/applications` prefix:

1. **POST /applications/** - Creates a new loan application (HTTP 202 Accepted)
   - Accepts: ApplicationReq (pan_number, applicant_name, monthly_income_inr, loan_amount_inr, loan_type)
   - Returns: Success message, application_id (UUID), and status
   - Automatically sets status to "pending" and timestamps
   - Publishes application to Kafka for async processing

2. **GET /applications/{application_id}/status** - Retrieves application status by UUID (HTTP 200)
   - Returns: application_id and current status
   - Raises 404 if application not found

### Dependency Injection

The codebase uses FastAPI's dependency injection pattern:
- `db_dependency = Annotated[Session, Depends(get_db)]` in `database.py:27`
- Router functions receive database sessions via the `db: db_dependency` parameter
- Sessions are automatically closed after request completion via generator pattern

### Validation

Pydantic models handle request validation:
- PAN number minimum length of 10 characters
- All monetary fields are required floats
- Field examples provided for API documentation

## Docker Configuration

The `docker-compose.yml` includes:
- **zookeeper**: Coordination service for Kafka (port 2181)
- **kafka**: Message broker (ports 9092 for host, 9093 for inter-container)
- **postgres**: Database (port 5432)
- **app**: FastAPI application (port 8000)

All services have health checks and proper dependency ordering. The application service mounts the current directory for hot-reload during development.

## Code Quality

This project uses Black and Ruff for code formatting and linting, enforced via pre-commit hooks.

### Configuration

- **pyproject.toml**: Contains Black and Ruff configuration (line length: 88, target: Python 3.13)
- **.pre-commit-config.yaml**: Pre-commit hooks configuration

### Manual Commands

To activate pre-commit in local after installing it:
```bash
 pre-commit install
```

Format code with Black:
```bash
black .
```

Check for linting issues with Ruff:
```bash
ruff check .
```

Auto-fix linting issues with Ruff:
```bash
ruff check --fix .
```

Run all pre-commit hooks manually:
```bash
pre-commit run --all-files
```

### Pre-commit Hooks

Pre-commit hooks are automatically installed and will run before each commit to:
- Format code with Black
- Check and fix linting issues with Ruff
- Check for trailing whitespace
- Fix end-of-file issues
- Validate YAML, JSON, and TOML files
- Check for merge conflicts

To bypass hooks (not recommended):
```bash
git commit --no-verify
```

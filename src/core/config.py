from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support and validation.

    All settings can be overridden via environment variables.
    """

    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_enabled: bool = True
    kafka_group_id: str = "loan_application_processor"
    loan_applications_topics: list[str] = [
        "loan_applications_submitted",
        "credit_reports_generated",
    ]

    # Database Configuration
    database_url: str = "postgresql://postgres:test1234@localhost:5432/LoanAppDatabase"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Application Configuration
    app_name: str = "Loan Prequalification Service"
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Map environment variables to snake_case field names
        env_prefix="",
    )


# Create a singleton instance
settings = Settings()

# Backwards compatibility with old config variables
KAFKA_BOOTSTRAP_SERVERS = settings.kafka_bootstrap_servers
LOAN_APPLICATIONS_TOPIC = settings.loan_applications_topics
KAFKA_ENABLED = settings.kafka_enabled
KAFKA_GROUP_ID = settings.kafka_group_id
SQLALCHEMY_DATABASE_URL = settings.database_url

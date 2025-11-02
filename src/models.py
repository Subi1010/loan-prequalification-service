import uuid
from datetime import UTC, datetime

from sqlalchemy import DECIMAL, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from src.core.app_status import ApplicationStatus
from src.database import Base


class Applications(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    pan_number = Column(String)
    applicant_name = Column(String)
    monthly_income_inr = Column(DECIMAL)
    loan_amount_inr = Column(DECIMAL)
    loan_type = Column(String)
    status = Column(String, default=ApplicationStatus.PENDING.value)
    cibil_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

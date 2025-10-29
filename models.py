from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app_status import ApplicationStatus


class Applications(Base):
    __tablename__ = 'applications'

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    pan_number = Column(String)
    applicant_name = Column(String)
    monthly_income_inr  = Column(DECIMAL)
    loan_amount_inr = Column(DECIMAL)
    loan_type = Column(String)
    status = Column(String, default=ApplicationStatus.PENDING.value)
    cibil_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

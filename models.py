from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, DECIMAL
from datetime import datetime


class Applications(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, index=True)
    pan_number = Column(String, unique=True)
    applicant_name = Column(String)
    monthly_income_inr  = Column(DECIMAL)
    loan_amount_inr = Column(DECIMAL)
    loan_type = Column(String)
    status = Column(String)
    cibil_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

from typing import Annotated
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Path
from starlette import status
from models import Applications
from database import get_db, db_dependency
from datetime import datetime
from app_status import ApplicationStatus


router = APIRouter(
    prefix='/applications',
    tags=['application']
)

class ApplicationReq(BaseModel):
    pan_number: str = Field(min_length=10, example="ABCDE1234F")
    applicant_name: str = Field(..., example="John Doe")
    monthly_income_inr: float = Field(..., example=50000.00)
    loan_amount_inr: float = Field(..., example=200000.00)
    loan_type: str = Field(..., example="PERSONAL")


@router.post('/', status_code=status.HTTP_201_CREATED)
def create_application(application: ApplicationReq, db: db_dependency):
    application = Applications(**application.dict(), status= ApplicationStatus.PENDING.value,created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(application)
    db.commit()
    return {"message": "Application created successfully", "application_id": application.id, "status": application.status}


@router.get('/{application_id}/status',status_code=status.HTTP_200_OK)
def get_application(application_id: str, db: db_dependency):
    application = db.query(Applications).filter(Applications.id == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return application.status

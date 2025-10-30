from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette import status

from app_status import ApplicationStatus
from database import db_dependency
from models import Applications

router = APIRouter(
    prefix='/applications',
    tags=['application']
)


class ApplicationReq(BaseModel):
    pan_number: str = Field(min_length=10, examples=["ABCDE1234F"])
    applicant_name: str = Field(..., examples=["John Doe"])
    monthly_income_inr: float = Field(..., examples=[50000.00])
    loan_amount_inr: float = Field(..., examples=[200000.00])
    loan_type: str = Field(..., examples=["PERSONAL"])


@router.post('/', status_code=status.HTTP_201_CREATED)
def create_application(application: ApplicationReq, db: db_dependency):
    application = Applications(
        **application.model_dump(),
        status=ApplicationStatus.PENDING.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(application)
    db.commit()
    return {
        "message": "Application created successfully",
        "application_id": application.id,
        "status": application.status
    }


@router.get('/{application_id}/status', status_code=status.HTTP_200_OK)
def get_application(application_id: str, db: db_dependency):
    application = db.query(Applications).filter(Applications.id == application_id).first()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return {"application_id": application.id, "status": application.status}

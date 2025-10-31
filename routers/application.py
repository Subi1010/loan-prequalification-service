import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette import status
import config as config

from app_status import ApplicationStatus
from database import db_dependency
from kafka_service.kafka_producer import send_data_to_kafka
from models import Applications

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["application"])


class ApplicationReq(BaseModel):
    pan_number: str = Field(
        min_length=10,
        examples=["ABCDE1234F"],
        message="PAN number is required and must be 10 characters long",
    )
    applicant_name: str = Field(..., examples=["John Doe"])
    monthly_income_inr: float = Field(..., examples=[50000.00])
    loan_amount_inr: float = Field(..., examples=[200000.00])
    loan_type: str = Field(..., examples=["PERSONAL"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
def create_application(application: ApplicationReq, db: db_dependency):
    # Create application in database
    db_application = Applications(
        **application.model_dump(),
        status=ApplicationStatus.PENDING.value,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(db_application)
    db.commit()

    # Prepare application data for Kafka
    application_data = {
        "id": str(db_application.id),
        "pan_number": db_application.pan_number,
        "applicant_name": db_application.applicant_name,
        "monthly_income_inr": float(db_application.monthly_income_inr),
        "loan_amount_inr": float(db_application.loan_amount_inr),
        "loan_type": db_application.loan_type,
        "status": db_application.status,
        "created_at": db_application.created_at.isoformat(),
        "updated_at": db_application.updated_at.isoformat(),
    }

    # Send application data to Kafka
    kafka_result = send_data_to_kafka(str(db_application.id), application_data, config.LOAN_APPLICATIONS_TOPIC[0])
    if not kafka_result:
        logger.warning(f"Failed to send application {db_application.id} to Kafka")

    return {
        "message": "Application created successfully",
        "application_id": db_application.id,
        "status": db_application.status,
    }


@router.get("/{application_id}/status", status_code=status.HTTP_200_OK)
def get_application(application_id: str, db: db_dependency):
    application = (
        db.query(Applications).filter(Applications.id == application_id).first()
    )
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    return {"application_id": application.id, "status": application.status}

"""
API endpoints for loan application operations.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from starlette import status

import src.core.config as config
from src.core.database import db_dependency
from src.core.logging_config import get_logger
from src.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusResponse,
)
from src.services.application_service import ApplicationService

logger = get_logger(__name__)
router = APIRouter(prefix="/applications", tags=["application"])


@router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ApplicationResponse,
    summary="Create a new loan application",
    description="Submit a new loan application for processing. The application will be asynchronously processed via Kafka.",
)
def create_application(
    application: ApplicationCreate, db: db_dependency
) -> ApplicationResponse:
    """
    Create a new loan application.

    Args:
        application: Application creation data
        db: Database session (injected)

    Returns:
        ApplicationResponse with application ID and status

    Raises:
        HTTPException: If application creation fails
    """
    try:
        # Use application service to create application
        service = ApplicationService(db)
        db_application = service.create_application(
            application, config.LOAN_APPLICATIONS_TOPIC[0]
        )

        return ApplicationResponse(
            message="Application created successfully",
            application_id=db_application.id,
            status=db_application.status,
        )
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application",
        ) from e


@router.get(
    "/{application_id}/status",
    status_code=status.HTTP_200_OK,
    response_model=ApplicationStatusResponse,
    summary="Get application status",
    description="Retrieve the current status of a loan application by its ID.",
)
def get_application_status(
    application_id: UUID, db: db_dependency
) -> ApplicationStatusResponse:
    """
    Get the status of a loan application.

    Args:
        application_id: UUID of the application
        db: Database session (injected)

    Returns:
        ApplicationStatusResponse with application ID and status

    Raises:
        HTTPException: If application not found
    """
    service = ApplicationService(db)
    application_status = service.get_application_status(application_id)

    if not application_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID {application_id} not found",
        )

    return application_status

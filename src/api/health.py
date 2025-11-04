"""
Health check endpoints for monitoring system status.
"""

from fastapi import APIRouter, status

from src.core.database import check_database_health
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="System health check",
    description="Check the health of various system components including database connectivity.",
)
def health_check():
    """
    Perform a health check of system components.

    Returns:
        Dict with health status of each component
    """
    logger.info("Health check requested")

    # Check database health
    health_status = check_database_health()

    # Return overall health status
    return health_status

from fastapi import APIRouter, Depends, Response, status

from app.api.dependencies import get_health_service
from app.schemas.health import HealthResponse
from app.services.health import HealthService

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "System is operational and database connectivity is verified",
            "model": HealthResponse,
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Database connectivity failed",
            "model": HealthResponse,
        },
    },
    summary="Service and Database Health Check Probe",
)
def check_health(
    response: Response,
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Verifies API service responsiveness and database reachability.

    Returns:
        HTTP 200 with status='healthy' if database is accessible.
        HTTP 503 with status='unhealthy' if database probe fails.
    """
    if not service.check_database():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unhealthy", database="disconnected")

    return HealthResponse(status="healthy", database="connected")

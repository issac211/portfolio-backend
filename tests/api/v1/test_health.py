from fastapi import status
from fastapi.testclient import TestClient

from app.api.dependencies import get_health_service
from app.main import app
from app.services.health import HealthService


def test_health_check_endpoint_healthy(client: TestClient) -> None:
    """Verifies that the health check endpoint returns 200 OK when database is reachable."""
    # Test versioned route
    response_v1 = client.get("/api/v1/health")
    assert response_v1.status_code == status.HTTP_200_OK
    data_v1 = response_v1.json()
    assert data_v1["status"] == "healthy"
    assert data_v1["database"] == "connected"

    # Test root alias route
    response_root = client.get("/health")
    assert response_root.status_code == status.HTTP_200_OK
    data_root = response_root.json()
    assert data_root["status"] == "healthy"
    assert data_root["database"] == "connected"


def test_health_check_endpoint_unhealthy(client: TestClient) -> None:
    """Verifies that the health check returns 503 Service Unavailable when database probe fails."""

    class FailingHealthService(HealthService):
        def check_database(self) -> bool:
            return False

    def override_health_service() -> FailingHealthService:
        # Pass dummy session since check_database will immediately return False
        return FailingHealthService(db=None)  # type: ignore[arg-type]

    app.dependency_overrides[get_health_service] = override_health_service
    try:
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
    finally:
        app.dependency_overrides.pop(get_health_service, None)

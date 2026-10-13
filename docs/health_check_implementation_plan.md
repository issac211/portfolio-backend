# Health Check Endpoint — Implementation Plan & Specification

## 1. Executive Summary & Objective

This document defines the architectural specification, design decisions, and implementation details for the **Production-Grade Health Check Endpoint** in the FastAPI backend.

The primary objective is to provide an ultra-lightweight, high-reliability health probe designed for:
1. **Automated Keep-Alive Pings:** Preventing cold starts on cloud providers (e.g., Render, Railway) via scheduled external pingers (GitHub Actions cron jobs, UptimeRobot).
2. **Container Orchestration Health Probes:** Enabling Docker Compose and Kubernetes liveness/readiness checks to monitor container health and restart failing instances automatically.
3. **Database Reachability Verification:** Validating true operational health (verifying that the backend can actively query the PostgreSQL database) rather than merely confirming that the HTTP server process is listening.

---

## 2. Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Layered Architecture (DDD)** | Separated into Schema, Service, Dependency, and Controller | Adheres strictly to the repository's Clean Architecture standards. Decouples raw SQL queries from HTTP routing. |
| **Connectivity Probe Query** | `SELECT 1` via SQLAlchemy 2.0 `Session.execute(text("SELECT 1"))` | Minimal overhead on the database engine while confirming connection pool validity, authentication, and network reachability. |
| **HTTP Status Semantics** | `200 OK` (Healthy) vs `503 Service Unavailable` (Unhealthy) | Adheres to RFC 9110. Automated monitoring tools and cloud load balancers recognize 5xx as unhealthy without parsing the JSON body. |
| **Route Aliasing** | Dual mounting: `/api/v1/health` and root `/health` | `/api/v1/health` follows standard API versioning; root `/health` accommodates external pingers and reverse proxies that assume standard conventions. |
| **Payload Schema** | Minimal JSON: `{"status": "...", "database": "..."}` | Keeps network payload under 50 bytes; avoids leaking internal database connection strings, credentials, or stack traces. |
| **Exception Handling** | Catch `Exception`, log warning, return graceful 503 | Prevents unhandled 500 errors or process crashes during temporary database blips. |

---

## 3. Component Specification & File Structure

```
backend/
├── docker-compose.yml             # Healthcheck probe updated to /api/v1/health
├── src/app/
│   ├── main.py                    # Routers mounted at /api/v1 and root /health
│   ├── api/
│   │   ├── dependencies.py        # get_health_service dependency factory
│   │   └── v1/
│   │       └── health.py          # HTTP GET controller with 200/503 status mapping
│   ├── schemas/
│   │   ├── __init__.py            # HealthResponse export
│   │   └── health.py              # HealthResponse Pydantic V2 model
│   └── services/
│       ├── __init__.py            # HealthService export
│       └── health.py              # HealthService domain business logic
└── tests/
    └── api/
        └── v1/
            └── test_health.py     # Unit & integration tests for healthy & degraded states
```

### 3.1 Pydantic Schema (`src/app/schemas/health.py`)
```python
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Schema representing service health and database connectivity status."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    database: str
```
- Exported via `src/app/schemas/__init__.py`.

### 3.2 Domain Service (`src/app/services/health.py`)
```python
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class HealthService:
    """Service encapsulating infrastructure and database health checks."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def check_database(self) -> bool:
        """Executes a lightweight query to verify active database reachability.

        Returns:
            bool: True if query succeeds, False otherwise.
        """
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.warning("Database health check probe failed: %s", e)
            return False
```
- Reuses the existing SQLAlchemy synchronous `Session` pool with zero overhead.
- Exported via `src/app/services/__init__.py`.

### 3.3 Dependency Injection (`src/app/api/dependencies.py`)
```python
def get_health_service(db: Session = Depends(get_db)) -> HealthService:
    """Provides an instantiated HealthService with a database session."""
    return HealthService(db)
```

### 3.4 API Controller (`src/app/api/v1/health.py`)
```python
from fastapi import APIRouter, Depends, Response, status
from app.api.dependencies import get_health_service
from app.schemas.health import HealthResponse
from app.services.health import HealthService

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check probe",
    description="Validates database connectivity and service operational status.",
)
def get_health(
    response: Response,
    health_service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Probes database connection and returns service health status."""
    is_db_connected = health_service.check_database()

    if not is_db_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unhealthy", database="disconnected")

    return HealthResponse(status="healthy", database="connected")
```

### 3.5 Routing Assembly (`src/app/main.py`)
```python
# Mounted under versioned API
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])

# Mounted at root level for external pingers and orchestrators
app.include_router(health.router, prefix="", tags=["Health"])
```

### 3.6 Docker Compose Healthcheck (`docker-compose.yml`)
```yaml
healthcheck:
  test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8000/api/v1/health\")'"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

---

## 4. Test Coverage & Verification (`tests/api/v1/test_health.py`)

Two comprehensive test scenarios are covered:
1. **Healthy Database (`test_health_check_healthy`):**
   - Sends `GET /api/v1/health` and `GET /health`.
   - Asserts HTTP status `200 OK`.
   - Asserts JSON response `{"status": "healthy", "database": "connected"}`.
2. **Database Failure / Degraded State (`test_health_check_database_down`):**
   - Mocks `HealthService.check_database` to return `False`.
   - Sends `GET /api/v1/health`.
   - Asserts HTTP status `503 Service Unavailable`.
   - Asserts JSON response `{"status": "unhealthy", "database": "disconnected"}`.

---

## 5. Implementation Checklist

- [x] Create `HealthResponse` schema in `src/app/schemas/health.py`.
- [x] Export `HealthResponse` in `src/app/schemas/__init__.py`.
- [x] Create `HealthService` with `check_database()` method in `src/app/services/health.py`.
- [x] Export `HealthService` in `src/app/services/__init__.py`.
- [x] Add `get_health_service` factory in `src/app/api/dependencies.py`.
- [x] Create `GET /health` endpoint controller in `src/app/api/v1/health.py`.
- [x] Mount health router in `src/app/main.py` under both `/api/v1` and root `/`.
- [x] Update `docker-compose.yml` healthcheck command to probe `/api/v1/health`.
- [x] Create automated test suite in `tests/api/v1/test_health.py`.
- [x] Ensure automated test isolation in `tests/conftest.py`.
- [x] Run test suite: `uv run pytest -v` (30/30 passed).
- [x] Verify linting rules: `uv run ruff check .` (0 errors).
- [x] Sync API contract: `frontend/api-contract.json` updated with new endpoints.

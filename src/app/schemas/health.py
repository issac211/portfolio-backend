from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Schema representing service health and database probe status."""

    status: str
    database: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "database": "connected",
            }
        }
    )

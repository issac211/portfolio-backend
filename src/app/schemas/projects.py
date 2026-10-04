from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1, max_length=300)
    content: str | None = None
    github_url: HttpUrl | None = None
    live_url: HttpUrl | None = None

    tags: list[str] | None = Field(
        default=None, description="List of tags / technologies used"
    )
    display_order: int | None = Field(default=None, ge=0)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    summary: str | None = Field(default=None, min_length=1, max_length=300)
    content: str | None = None
    github_url: HttpUrl | None = None
    live_url: HttpUrl | None = None
    tags: list[str] | None = None
    display_order: int | None = Field(default=None, ge=0)


class ProjectResponse(ProjectBase):
    id: int
    image_url: str | None = None

    # Allows Pydantic to read data from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PersonalInfoBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    birth_date: date | None = None
    bio: str | None = Field(default=None, max_length=2000)
    hero_title: str | None = Field(default=None, max_length=200)
    availability_status: str | None = Field(default=None, max_length=100)
    short_bio: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    status_indicator: Literal["success", "warning", "error", "neutral"] | None = (
        "neutral"
    )


class PersonalInfoCreate(PersonalInfoBase):
    pass


class PersonalInfoUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    birth_date: date | None = None
    bio: str | None = Field(default=None, max_length=2000)
    hero_title: str | None = Field(default=None, max_length=200)
    availability_status: str | None = Field(default=None, max_length=100)
    short_bio: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    status_indicator: Literal["success", "warning", "error", "neutral"] | None = None


class PersonalInfoResponse(PersonalInfoBase):
    id: int
    image_url: str | None = None
    is_active: bool

    # Allows Pydantic to read data from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)

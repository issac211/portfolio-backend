from datetime import date

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PersonalInfoBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    birth_date: date | None = None
    bio: str | None = Field(default=None, max_length=2000)
    image_url: HttpUrl | None = None


class PersonalInfoCreate(PersonalInfoBase):
    pass


class PersonalInfoUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    birth_date: date | None = None
    bio: str | None = Field(default=None, max_length=2000)
    image_url: HttpUrl | None = None


class PersonalInfoResponse(PersonalInfoBase):
    id: int

    # Allows Pydantic to read data from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)

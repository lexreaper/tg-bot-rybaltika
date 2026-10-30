from datetime import date as DateValue, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    date: DateValue
    image_url: str | None


class VacancyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    position: str
    description: str
    salary: str | None


class LoyaltyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: str
    summary: str
    body: str
    updated_at: datetime | None


class LoyaltyAdminRead(LoyaltyRead):
    is_published: bool
    version: int


class LoyaltyUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(max_length=300)
    body: str = Field(min_length=1, max_length=10000)
    is_published: bool
    expected_version: int = Field(ge=0)

    @field_validator('title', 'summary', 'body', mode='before')
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

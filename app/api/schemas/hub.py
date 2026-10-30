from datetime import datetime
from typing import ClassVar, Self

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class ReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PatchSchema(InputSchema):
    required_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        for field in self.required_fields & self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


def _require_timezone(value: datetime | None) -> datetime | None:
    if value is not None and value.utcoffset() is None:
        raise ValueError("Datetime values must include a timezone")
    return value


class BarRead(ReadSchema):
    id: int
    slug: str
    name: str
    website_url: str
    description: str | None
    logo_url: str | None
    is_published: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class BarCreate(InputSchema):
    slug: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    name: str = Field(min_length=1, max_length=150)
    website_url: AnyHttpUrl
    description: str | None = None
    logo_url: AnyHttpUrl | None = None
    is_published: bool = False
    sort_order: int = Field(default=0, ge=0)


class BarUpdate(PatchSchema):
    required_fields: ClassVar[frozenset[str]] = frozenset(
        {"slug", "name", "website_url", "is_published", "sort_order"}
    )

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    name: str | None = Field(default=None, min_length=1, max_length=150)
    website_url: AnyHttpUrl | None = None
    description: str | None = None
    logo_url: AnyHttpUrl | None = None
    is_published: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class EventRead(ReadSchema):
    id: int
    bar_id: int | None
    title: str
    description: str
    starts_at: datetime
    ends_at: datetime | None
    location: str | None
    image_url: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class EventCreate(InputSchema):
    bar_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime | None = None
    location: str | None = Field(default=None, max_length=200)
    image_url: AnyHttpUrl | None = None
    is_published: bool = False

    _validate_starts_at = field_validator("starts_at")(_require_timezone)
    _validate_ends_at = field_validator("ends_at")(_require_timezone)

    @model_validator(mode="after")
    def validate_event_dates(self) -> Self:
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self


class EventUpdate(PatchSchema):
    required_fields: ClassVar[frozenset[str]] = frozenset(
        {"title", "description", "starts_at", "is_published"}
    )

    bar_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location: str | None = Field(default=None, max_length=200)
    image_url: AnyHttpUrl | None = None
    is_published: bool | None = None

    _validate_starts_at = field_validator("starts_at")(_require_timezone)
    _validate_ends_at = field_validator("ends_at")(_require_timezone)

    @model_validator(mode="after")
    def validate_event_dates(self) -> Self:
        if (
            self.starts_at is not None
            and self.ends_at is not None
            and self.ends_at <= self.starts_at
        ):
            raise ValueError("ends_at must be later than starts_at")
        return self


class VacancyRead(ReadSchema):
    id: int
    bar_id: int | None
    title: str
    description: str
    employment_type: str | None
    salary: str | None
    contact_email: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class VacancyCreate(InputSchema):
    bar_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    employment_type: str | None = Field(default=None, max_length=100)
    salary: str | None = Field(default=None, max_length=200)
    contact_email: str | None = Field(
        default=None,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    is_published: bool = False


class VacancyUpdate(PatchSchema):
    required_fields: ClassVar[frozenset[str]] = frozenset(
        {"title", "description", "is_published"}
    )

    bar_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    employment_type: str | None = Field(default=None, max_length=100)
    salary: str | None = Field(default=None, max_length=200)
    contact_email: str | None = Field(
        default=None,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    is_published: bool | None = None


class LoyaltyInfoRead(ReadSchema):
    id: int
    key: str
    title: str
    content: str
    terms_url: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class LoyaltyInfoCreate(InputSchema):
    key: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    terms_url: AnyHttpUrl | None = None
    is_published: bool = False


class LoyaltyInfoUpdate(PatchSchema):
    required_fields: ClassVar[frozenset[str]] = frozenset(
        {"key", "title", "content", "is_published"}
    )

    key: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    terms_url: AnyHttpUrl | None = None
    is_published: bool | None = None


def sqlalchemy_values(
    schema: InputSchema, *, exclude_unset: bool = False
) -> dict[str, object]:
    values = schema.model_dump(exclude_unset=exclude_unset)
    return {
        name: str(value)
        if name.endswith("_url") and value is not None
        else value
        for name, value in values.items()
    }

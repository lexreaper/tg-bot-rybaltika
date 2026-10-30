from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str | None
    price: Decimal
    image_url: str | None
    is_available: bool


class DishCreate(BaseModel):
    name: str
    category_id: int
    description: str | None
    price: Decimal
    image_url: str | None
    is_available: bool = True

class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    sort_order: int
    dish_count: int
    image_url: str | None

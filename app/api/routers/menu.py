from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import Category, Dish
from app.db.session import get_session
from app.api.schemas.menu import DishRead, DishCreate

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=list[DishRead])
async def get_menu(
    session: Annotated[AsyncSession, Depends(get_session)],
    category_id: Annotated[int | None, Query(ge=1)] = None,
) -> list[DishRead]:
    statement = (
        select(Dish)
        .join(Dish.category)
        .where(Dish.is_available.is_(True))
        .order_by(Category.sort_order, Dish.id)
    )
    if category_id is not None:
        statement = statement.where(Dish.category_id == category_id)

    dishes = await session.scalars(statement)
    return [DishRead.model_validate(dish) for dish in dishes]


router.post("/dishes", response_model=DishRead)
async def create_dish(
    session: Annotated[AsyncSession, Depends(get_session)],
    dish: DishCreate,
) -> DishRead:
    db_dish = Dish(**dish.model_dump())
    session.add(db_dish)
    await session.commit()
    await session.refresh(db_dish)
    return DishRead.model_validate(db_dish)
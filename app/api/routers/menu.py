from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import dish_crud
from app.db.session import get_session
from app.api.schemas.menu import DishRead, DishCreate

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=list[DishRead])
async def get_menu(
    session: Annotated[AsyncSession, Depends(get_session)],
    category_id: Annotated[int | None, Query(ge=1)] = None,
) -> list[DishRead]:
    dishes = await dish_crud.get_menu(session, category_id=category_id)
    return [DishRead.model_validate(dish) for dish in dishes]


@router.get("/dishes/{dish_id}", response_model=DishRead)
async def get_dish(
    dish_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DishRead:
    dish = await dish_crud.get_available(session, dish_id)
    if dish is None:
        raise HTTPException(status_code=404, detail="Блюдо не найдено")
    return DishRead.model_validate(dish)


@router.post("/dishes", response_model=DishRead, status_code=201)
async def create_dish(
    session: Annotated[AsyncSession, Depends(get_session)],
    dish: DishCreate,
) -> DishRead:
    db_dish = await dish_crud.create(session, dish.model_dump())
    await session.commit()
    return DishRead.model_validate(db_dish)
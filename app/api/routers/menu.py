from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.model import Category, Dish

from app.db.crud import dish_crud
from app.db.session import get_session
from app.api.schemas.menu import DishRead, DishCreate, CategoryRead

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=list[DishRead])
async def get_menu(
    session: Annotated[AsyncSession, Depends(get_session)],
    category_id: Annotated[int | None, Query(ge=1)] = None,
) -> list[DishRead]:
    if category_id is not None and await session.get(Category, category_id) is None:
        raise HTTPException(status_code=404, detail="Категория не найдена")
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

@router.get("/categories", response_model=list[CategoryRead])
async def get_categories(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[CategoryRead]:
    # Include empty categories; count and cover only currently available dishes.
    count = select(func.count(Dish.id)).where(
        Dish.category_id == Category.id, Dish.is_available.is_(True)
    ).correlate(Category).scalar_subquery()
    cover = select(Dish.image_url).where(
        Dish.category_id == Category.id, Dish.is_available.is_(True),
        Dish.image_url.is_not(None), Dish.image_url != "",
    ).order_by(Dish.id).limit(1).correlate(Category).scalar_subquery()
    rows = await session.execute(select(Category, count, cover).order_by(Category.sort_order, Category.id))
    return [CategoryRead(id=c.id, name=c.name, sort_order=c.sort_order,
                         dish_count=n, image_url=url) for c, n, url in rows]

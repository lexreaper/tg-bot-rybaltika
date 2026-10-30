from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.base import CRUDBase
from app.db.model import Category, Dish


class DishCRUD(CRUDBase[Dish]):
    async def get_menu(
        self, session: AsyncSession, *, category_id: int | None = None
    ) -> list[Dish]:
        statement = (
            select(Dish)
            .join(Dish.category)
            .where(Dish.is_available.is_(True))
            .order_by(Category.sort_order, Dish.id)
        )
        if category_id is not None:
            statement = statement.where(Dish.category_id == category_id)

        result = await session.scalars(statement)
        return list(result)

    async def get_available(
        self, session: AsyncSession, dish_id: int
    ) -> Dish | None:
        statement = select(Dish).where(
            Dish.id == dish_id,
            Dish.is_available.is_(True),
        )
        return await session.scalar(statement)

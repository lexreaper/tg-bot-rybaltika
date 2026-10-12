from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model
        self._column_names = {column.key for column in model.__mapper__.column_attrs}
        self._primary_key = model.__mapper__.primary_key[0].key

    def _validate_fields(self, data: dict[str, Any]) -> None:
        invalid_fields = data.keys() - self._column_names
        if invalid_fields:
            fields = ", ".join(sorted(invalid_fields))
            raise ValueError(f"Unknown {self.model.__name__} field(s): {fields}")

    async def create(
        self, session: AsyncSession, data: dict[str, Any]
    ) -> ModelType:
        self._validate_fields(data)
        instance = self.model(**data)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def get(self, session: AsyncSession, object_id: int) -> ModelType | None:
        return await session.get(self.model, object_id)

    async def get_by(
        self, session: AsyncSession, **filters: Any
    ) -> ModelType | None:
        if not filters:
            raise ValueError("At least one filter is required")
        self._validate_fields(filters)
        statement = select(self.model).filter_by(**filters)
        return await session.scalar(statement)

    async def get_multi(
        self, session: AsyncSession, *, offset: int = 0, limit: int = 100
    ) -> list[ModelType]:
        if offset < 0:
            raise ValueError("offset must be non-negative")
        if limit < 1:
            raise ValueError("limit must be positive")

        statement = (
            select(self.model)
            .order_by(getattr(self.model, self._primary_key))
            .offset(offset)
            .limit(limit)
        )
        result = await session.scalars(statement)
        return list(result)

    async def update(
        self, session: AsyncSession, object_id: int, data: dict[str, Any]
    ) -> ModelType | None:
        self._validate_fields(data)
        if self._primary_key in data:
            raise ValueError(f"Cannot update primary key '{self._primary_key}'")

        instance = await self.get(session, object_id)
        if instance is None:
            return None

        for field, value in data.items():
            setattr(instance, field, value)
        await session.flush()
        return instance

    async def delete(self, session: AsyncSession, object_id: int) -> bool:
        instance = await self.get(session, object_id)
        if instance is None:
            return False

        await session.delete(instance)
        await session.flush()
        return True

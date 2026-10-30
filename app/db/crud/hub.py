from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.base import CRUDBase
from app.db.model import Bar, Event, LoyaltyInfo, Vacancy


class BarCRUD(CRUDBase[Bar]):
    async def get_published(
        self, session: AsyncSession, *, offset: int = 0, limit: int = 100
    ) -> list[Bar]:
        statement = (
            select(Bar)
            .where(Bar.is_published.is_(True))
            .order_by(Bar.sort_order, Bar.name)
            .offset(offset)
            .limit(limit)
        )
        return list(await session.scalars(statement))


class EventCRUD(CRUDBase[Event]):
    async def get_published(
        self,
        session: AsyncSession,
        *,
        bar_id: int | None = None,
        upcoming_only: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Event]:
        statement = select(Event).where(Event.is_published.is_(True))
        if bar_id is not None:
            statement = statement.where(Event.bar_id == bar_id)
        if upcoming_only:
            statement = statement.where(Event.starts_at >= datetime.now(UTC))
        statement = (
            statement.order_by(Event.starts_at, Event.id)
            .offset(offset)
            .limit(limit)
        )
        return list(await session.scalars(statement))

    async def get_published_by_id(
        self, session: AsyncSession, event_id: int
    ) -> Event | None:
        statement = select(Event).where(
            Event.id == event_id,
            Event.is_published.is_(True),
        )
        return await session.scalar(statement)


class VacancyCRUD(CRUDBase[Vacancy]):
    async def get_published(
        self, session: AsyncSession, *, offset: int = 0, limit: int = 100
    ) -> list[Vacancy]:
        statement = (
            select(Vacancy)
            .where(Vacancy.is_published.is_(True))
            .order_by(Vacancy.created_at.desc(), Vacancy.id)
            .offset(offset)
            .limit(limit)
        )
        return list(await session.scalars(statement))


class LoyaltyInfoCRUD(CRUDBase[LoyaltyInfo]):
    async def get_published(
        self, session: AsyncSession, *, offset: int = 0, limit: int = 100
    ) -> list[LoyaltyInfo]:
        statement = (
            select(LoyaltyInfo)
            .where(LoyaltyInfo.is_published.is_(True))
            .order_by(LoyaltyInfo.id)
            .offset(offset)
            .limit(limit)
        )
        return list(await session.scalars(statement))

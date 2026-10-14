from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] | None = getattr(
        request.app.state, "session_factory", None
    )
    if session_factory is None:
        raise RuntimeError("Database session factory is not configured")

    async with session_factory() as session:
        yield session

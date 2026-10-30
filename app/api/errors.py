from collections.abc import Awaitable
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

Result = TypeVar("Result")


async def save_or_conflict(
    session: AsyncSession, operation: Awaitable[Result]
) -> Result:
    try:
        result = await operation
        await session.commit()
        return result
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=409,
            detail="The change conflicts with existing data",
        ) from exc

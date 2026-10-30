from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.hub import (
    BarRead,
    EventRead,
    LoyaltyInfoRead,
    VacancyRead,
)
from app.db.crud import bar_crud, event_crud, loyalty_info_crud, vacancy_crud
from app.db.session import get_session

router = APIRouter(tags=["public"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
EventId = Annotated[int, Path(ge=1)]


@router.get("/bars", response_model=list[BarRead])
async def get_bars(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[BarRead]:
    bars = await bar_crud.get_published(session, offset=offset, limit=limit)
    return [BarRead.model_validate(bar) for bar in bars]


@router.get("/events", response_model=list[EventRead])
async def get_events(
    session: SessionDep,
    bar_id: Annotated[int | None, Query(ge=1)] = None,
    upcoming_only: bool = True,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[EventRead]:
    events = await event_crud.get_published(
        session,
        bar_id=bar_id,
        upcoming_only=upcoming_only,
        offset=offset,
        limit=limit,
    )
    return [EventRead.model_validate(event) for event in events]


@router.get("/events/{event_id}", response_model=EventRead)
async def get_event(event_id: EventId, session: SessionDep) -> EventRead:
    event = await event_crud.get_published_by_id(session, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventRead.model_validate(event)


@router.get("/vacancies", response_model=list[VacancyRead])
async def get_vacancies(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[VacancyRead]:
    vacancies = await vacancy_crud.get_published(
        session, offset=offset, limit=limit
    )
    return [VacancyRead.model_validate(vacancy) for vacancy in vacancies]


@router.get("/loyalty", response_model=list[LoyaltyInfoRead])
async def get_loyalty_info(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[LoyaltyInfoRead]:
    information = await loyalty_info_crud.get_published(
        session, offset=offset, limit=limit
    )
    return [LoyaltyInfoRead.model_validate(item) for item in information]

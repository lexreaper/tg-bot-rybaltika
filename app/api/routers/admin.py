from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_admin
from app.api.errors import save_or_conflict
from app.api.schemas.hub import (
    BarCreate,
    BarRead,
    BarUpdate,
    EventCreate,
    EventRead,
    EventUpdate,
    LoyaltyInfoCreate,
    LoyaltyInfoRead,
    LoyaltyInfoUpdate,
    VacancyCreate,
    VacancyRead,
    VacancyUpdate,
    sqlalchemy_values,
)
from app.db.crud import bar_crud, event_crud, loyalty_info_crud, vacancy_crud
from app.db.session import get_session

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)
SessionDep = Annotated[AsyncSession, Depends(get_session)]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]
RecordId = Annotated[int, Path(ge=1)]


@router.get("/bars", response_model=list[BarRead])
async def admin_get_bars(
    session: SessionDep, offset: Offset = 0, limit: Limit = 100
) -> list[BarRead]:
    records = await bar_crud.get_multi(session, offset=offset, limit=limit)
    return [BarRead.model_validate(record) for record in records]


@router.post("/bars", response_model=BarRead, status_code=201)
async def admin_create_bar(body: BarCreate, session: SessionDep) -> BarRead:
    record = await save_or_conflict(
        session,
        bar_crud.create(session, sqlalchemy_values(body)),
    )
    return BarRead.model_validate(record)


@router.get("/bars/{bar_id}", response_model=BarRead)
async def admin_get_bar(bar_id: RecordId, session: SessionDep) -> BarRead:
    record = await bar_crud.get(session, bar_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Bar not found")
    return BarRead.model_validate(record)


@router.patch("/bars/{bar_id}", response_model=BarRead)
async def admin_update_bar(
    bar_id: RecordId, body: BarUpdate, session: SessionDep
) -> BarRead:
    record = await save_or_conflict(
        session,
        bar_crud.update(session, bar_id, sqlalchemy_values(body, exclude_unset=True)),
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Bar not found")
    await session.refresh(record)
    return BarRead.model_validate(record)


@router.delete("/bars/{bar_id}", status_code=204)
async def admin_delete_bar(bar_id: RecordId, session: SessionDep) -> None:
    deleted = await save_or_conflict(session, bar_crud.delete(session, bar_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Bar not found")


@router.get("/events", response_model=list[EventRead])
async def admin_get_events(
    session: SessionDep, offset: Offset = 0, limit: Limit = 100
) -> list[EventRead]:
    records = await event_crud.get_multi(session, offset=offset, limit=limit)
    return [EventRead.model_validate(record) for record in records]


@router.post("/events", response_model=EventRead, status_code=201)
async def admin_create_event(body: EventCreate, session: SessionDep) -> EventRead:
    record = await save_or_conflict(
        session,
        event_crud.create(session, sqlalchemy_values(body)),
    )
    return EventRead.model_validate(record)


@router.get("/events/{event_id}", response_model=EventRead)
async def admin_get_event(event_id: RecordId, session: SessionDep) -> EventRead:
    record = await event_crud.get(session, event_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventRead.model_validate(record)


@router.patch("/events/{event_id}", response_model=EventRead)
async def admin_update_event(
    event_id: RecordId, body: EventUpdate, session: SessionDep
) -> EventRead:
    existing = await event_crud.get(session, event_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Event not found")
    changes = sqlalchemy_values(body, exclude_unset=True)
    starts_at = body.starts_at or existing.starts_at
    ends_at = (
        body.ends_at
        if "ends_at" in body.model_fields_set
        else existing.ends_at
    )
    if ends_at is not None and ends_at <= starts_at:
        raise HTTPException(
            status_code=422,
            detail="ends_at must be later than starts_at",
        )

    record = await save_or_conflict(
        session,
        event_crud.update(session, event_id, changes),
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Event not found")
    await session.refresh(record)
    return EventRead.model_validate(record)


@router.delete("/events/{event_id}", status_code=204)
async def admin_delete_event(event_id: RecordId, session: SessionDep) -> None:
    deleted = await save_or_conflict(session, event_crud.delete(session, event_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")


@router.get("/vacancies", response_model=list[VacancyRead])
async def admin_get_vacancies(
    session: SessionDep, offset: Offset = 0, limit: Limit = 100
) -> list[VacancyRead]:
    records = await vacancy_crud.get_multi(session, offset=offset, limit=limit)
    return [VacancyRead.model_validate(record) for record in records]


@router.post("/vacancies", response_model=VacancyRead, status_code=201)
async def admin_create_vacancy(
    body: VacancyCreate, session: SessionDep
) -> VacancyRead:
    record = await save_or_conflict(
        session,
        vacancy_crud.create(session, sqlalchemy_values(body)),
    )
    return VacancyRead.model_validate(record)


@router.get("/vacancies/{vacancy_id}", response_model=VacancyRead)
async def admin_get_vacancy(vacancy_id: RecordId, session: SessionDep) -> VacancyRead:
    record = await vacancy_crud.get(session, vacancy_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return VacancyRead.model_validate(record)


@router.patch("/vacancies/{vacancy_id}", response_model=VacancyRead)
async def admin_update_vacancy(
    vacancy_id: RecordId, body: VacancyUpdate, session: SessionDep
) -> VacancyRead:
    record = await save_or_conflict(
        session,
        vacancy_crud.update(
            session,
            vacancy_id,
            sqlalchemy_values(body, exclude_unset=True),
        ),
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    await session.refresh(record)
    return VacancyRead.model_validate(record)


@router.delete("/vacancies/{vacancy_id}", status_code=204)
async def admin_delete_vacancy(vacancy_id: RecordId, session: SessionDep) -> None:
    deleted = await save_or_conflict(
        session, vacancy_crud.delete(session, vacancy_id)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Vacancy not found")


@router.get("/loyalty", response_model=list[LoyaltyInfoRead])
async def admin_get_loyalty(
    session: SessionDep, offset: Offset = 0, limit: Limit = 100
) -> list[LoyaltyInfoRead]:
    records = await loyalty_info_crud.get_multi(
        session, offset=offset, limit=limit
    )
    return [LoyaltyInfoRead.model_validate(record) for record in records]


@router.post("/loyalty", response_model=LoyaltyInfoRead, status_code=201)
async def admin_create_loyalty(
    body: LoyaltyInfoCreate, session: SessionDep
) -> LoyaltyInfoRead:
    record = await save_or_conflict(
        session,
        loyalty_info_crud.create(session, sqlalchemy_values(body)),
    )
    return LoyaltyInfoRead.model_validate(record)


@router.get("/loyalty/{loyalty_id}", response_model=LoyaltyInfoRead)
async def admin_get_loyalty_item(
    loyalty_id: RecordId, session: SessionDep
) -> LoyaltyInfoRead:
    record = await loyalty_info_crud.get(session, loyalty_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Loyalty information not found")
    return LoyaltyInfoRead.model_validate(record)


@router.patch("/loyalty/{loyalty_id}", response_model=LoyaltyInfoRead)
async def admin_update_loyalty(
    loyalty_id: RecordId, body: LoyaltyInfoUpdate, session: SessionDep
) -> LoyaltyInfoRead:
    record = await save_or_conflict(
        session,
        loyalty_info_crud.update(
            session,
            loyalty_id,
            sqlalchemy_values(body, exclude_unset=True),
        ),
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Loyalty information not found")
    await session.refresh(record)
    return LoyaltyInfoRead.model_validate(record)


@router.delete("/loyalty/{loyalty_id}", status_code=204)
async def admin_delete_loyalty(
    loyalty_id: RecordId, session: SessionDep
) -> None:
    deleted = await save_or_conflict(
        session, loyalty_info_crud.delete(session, loyalty_id)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Loyalty information not found")

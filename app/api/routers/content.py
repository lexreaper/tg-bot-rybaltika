"""Public reads for the new frontend; only the loyalty editor writes content.

Event/vacancy CRUD and a general admin panel remain separate team tasks.
"""
from datetime import datetime, timezone
from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.content import EventRead, LoyaltyAdminRead, LoyaltyRead, LoyaltyUpdate, VacancyRead
from app.db.content import Event, LoyaltyPage, Vacancy
from app.db.session import get_session
from app.settings import get_app_settings

router = APIRouter(tags=['content'])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get('/events', response_model=list[EventRead])
async def events(session: Session):
    return list(await session.scalars(select(Event).where(Event.is_published.is_(True)).order_by(Event.event_date, Event.id)))


@router.get('/vacancies', response_model=list[VacancyRead])
async def vacancies(session: Session):
    return list(await session.scalars(select(Vacancy).where(Vacancy.is_published.is_(True)).order_by(Vacancy.id)))


@router.get('/loyalty', response_model=LoyaltyRead | None)
async def loyalty(session: Session):
    page = await session.get(LoyaltyPage, 1)
    return page if page is not None and page.is_published else None


async def require_content_admin(token: Annotated[str | None, Header(alias='X-Admin-Token')] = None):
    expected = get_app_settings().content_admin_token
    if expected is None:
        raise HTTPException(503, 'Редактор не настроен на сервере. Обратитесь к администратору.')
    if token is None or not compare_digest(token.encode(), expected.get_secret_value().encode()):
        raise HTTPException(401, 'Неверный ключ доступа')


@router.get('/admin/loyalty', response_model=LoyaltyAdminRead, dependencies=[Depends(require_content_admin)])
async def admin_loyalty(session: Session):
    return await session.get(LoyaltyPage, 1) or LoyaltyAdminRead(
        title='', summary='', body='', updated_at=None, is_published=False, version=0,
    )


@router.put('/admin/loyalty', response_model=LoyaltyAdminRead, dependencies=[Depends(require_content_admin)])
async def update_loyalty(data: LoyaltyUpdate, session: Session):
    values = data.model_dump(exclude={'expected_version'})
    values['updated_at'] = datetime.now(timezone.utc)
    page = await session.get(LoyaltyPage, 1)
    if page is None:
        if data.expected_version != 0:
            raise HTTPException(409, 'Страница изменилась. Загрузите актуальную версию.')
        page = LoyaltyPage(id=1, version=1, **values)
        session.add(page)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(409, 'Страница уже создана. Загрузите актуальную версию.') from exc
    else:
        result = await session.execute(update(LoyaltyPage).where(
            LoyaltyPage.id == 1, LoyaltyPage.version == data.expected_version,
        ).values(**values, version=LoyaltyPage.version + 1))
        if result.rowcount != 1:
            await session.rollback()
            raise HTTPException(409, 'Страница изменилась. Загрузите актуальную версию.')
        await session.commit()
    await session.refresh(page)
    return page

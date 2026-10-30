"""Compatibility API consumed by the existing Mini App frontend."""

from datetime import UTC, datetime
from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.content import (
    EventRead,
    LoyaltyAdminRead,
    LoyaltyRead,
    LoyaltyUpdate,
    VacancyRead,
)
from app.db.model import Event, LoyaltyInfo, Vacancy
from app.db.session import get_session
from app.settings import get_app_settings

router = APIRouter(tags=["content"])
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/events", response_model=list[EventRead])
async def events(session: Session) -> list[EventRead]:
    records = await session.scalars(
        select(Event)
        .where(Event.is_published.is_(True))
        .order_by(Event.starts_at, Event.id)
    )
    return [
        EventRead(
            id=event.id,
            title=event.title,
            description=event.description,
            date=event.starts_at.date(),
            image_url=event.image_url,
        )
        for event in records
    ]


@router.get("/vacancies", response_model=list[VacancyRead])
async def vacancies(session: Session) -> list[VacancyRead]:
    records = await session.scalars(
        select(Vacancy)
        .where(Vacancy.is_published.is_(True))
        .order_by(Vacancy.id)
    )
    return [
        VacancyRead(
            id=vacancy.id,
            position=vacancy.title,
            description=vacancy.description,
            salary=vacancy.salary,
        )
        for vacancy in records
    ]


@router.get("/loyalty", response_model=LoyaltyRead | None)
async def loyalty(session: Session) -> LoyaltyRead | None:
    page = await session.scalar(
        select(LoyaltyInfo).where(
            LoyaltyInfo.key == "loyalty",
            LoyaltyInfo.is_published.is_(True),
        )
    )
    if page is None:
        return None
    return LoyaltyRead(
        title=page.title,
        summary=page.summary,
        body=page.content,
        updated_at=page.updated_at,
    )


async def require_content_admin(
    token: Annotated[str | None, Header(alias="X-Admin-Token")] = None,
) -> None:
    expected = get_app_settings().content_admin_token
    if expected is None:
        raise HTTPException(
            503,
            "Редактор не настроен на сервере. Обратитесь к администратору.",
        )
    if token is None or not compare_digest(
        token.encode(),
        expected.get_secret_value().encode(),
    ):
        raise HTTPException(401, "Неверный ключ доступа")


def _editor_read(page: LoyaltyInfo | None) -> LoyaltyAdminRead:
    if page is None:
        return LoyaltyAdminRead(
            title="",
            summary="",
            body="",
            updated_at=None,
            is_published=False,
            version=0,
        )
    return LoyaltyAdminRead(
        title=page.title,
        summary=page.summary,
        body=page.content,
        updated_at=page.updated_at,
        is_published=page.is_published,
        version=page.version,
    )


async def _get_editor_page(session: AsyncSession) -> LoyaltyInfo | None:
    return await session.scalar(
        select(LoyaltyInfo).where(LoyaltyInfo.key == "loyalty")
    )


@router.get(
    "/admin/loyalty",
    response_model=LoyaltyAdminRead,
    dependencies=[Depends(require_content_admin)],
)
async def admin_loyalty(session: Session) -> LoyaltyAdminRead:
    return _editor_read(await _get_editor_page(session))


@router.put(
    "/admin/loyalty",
    response_model=LoyaltyAdminRead,
    dependencies=[Depends(require_content_admin)],
)
async def update_loyalty(
    data: LoyaltyUpdate,
    session: Session,
) -> LoyaltyAdminRead:
    page = await _get_editor_page(session)
    values = data.model_dump(exclude={"expected_version"})
    updated_at = datetime.now(UTC)

    if page is None:
        if data.expected_version != 0:
            raise HTTPException(
                409,
                "Страница изменилась. Загрузите актуальную версию.",
            )
        page = LoyaltyInfo(
            key="loyalty",
            title=values["title"],
            summary=values["summary"],
            content=values["body"],
            is_published=values["is_published"],
            version=1,
            updated_at=updated_at,
        )
        session.add(page)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                409,
                "Страница уже создана. Загрузите актуальную версию.",
            ) from exc
    else:
        result = await session.execute(
            update(LoyaltyInfo)
            .where(
                LoyaltyInfo.id == page.id,
                LoyaltyInfo.version == data.expected_version,
            )
            .values(
                title=values["title"],
                summary=values["summary"],
                content=values["body"],
                is_published=values["is_published"],
                version=LoyaltyInfo.version + 1,
                updated_at=updated_at,
            )
        )
        if result.rowcount != 1:
            await session.rollback()
            raise HTTPException(
                409,
                "Страница изменилась. Загрузите актуальную версию.",
            )
        await session.commit()

    await session.refresh(page)
    return _editor_read(page)

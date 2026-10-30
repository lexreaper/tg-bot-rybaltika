"""Insert sample records into empty menu and hub tables."""

import asyncio

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.config import get_database_settings
from app.db.model import Base, Bar, Category, Dish, Event, LoyaltyInfo, Vacancy
from app.demo import seed_demo
from app.demo_content import seed_demo_content


TEST_BARS = (
    Bar(
        slug="test-bar-center",
        name="Тестовый бар — Центр",
        website_url="https://example.invalid/test-bar-center",
        description="Тестовая запись для проверки API хаба.",
        is_published=True,
        sort_order=1,
    ),
    Bar(
        slug="test-bar-north",
        name="Тестовый бар — Север",
        website_url="https://example.invalid/test-bar-north",
        description="Тестовая запись для проверки списка баров.",
        is_published=True,
        sort_order=2,
    ),
)


async def row_count(session, model: type[Base]) -> int:
    return await session.scalar(select(func.count()).select_from(model)) or 0


async def seed_bars(session) -> None:
    if await row_count(session, Bar):
        print("Бары: таблица уже содержит данные, пропускаю.")
        return

    session.add_all(TEST_BARS)
    await session.commit()
    print(f"Бары: добавлено тестовых записей — {len(TEST_BARS)}.")


async def seed_menu_if_empty(session) -> None:
    before = await row_count(session, Category)
    await seed_demo(session)
    after = await row_count(session, Category)
    if after > before:
        print(
            f"Меню: добавлено категорий — {after - before}, "
            f"блюд — {await row_count(session, Dish)}."
        )
    else:
        print("Меню: категории уже есть, раздел не изменён.")


async def seed_hub_content_if_empty(session) -> None:
    models = (
        ("Мероприятия", Event),
        ("Вакансии", Vacancy),
        ("Лояльность", LoyaltyInfo),
    )
    before = {
        model: await row_count(session, model)
        for _, model in models
    }
    await seed_demo_content(session)
    for label, model in models:
        added = await row_count(session, model) - before[model]
        if added:
            print(f"{label}: добавлено записей — {added}.")
        else:
            print(f"{label}: данные уже есть, раздел не изменён.")


async def main() -> None:
    database_url = get_database_settings().sqlalchemy_url
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            print(
                "Добавляю тестовые данные только в пустые разделы. "
                "Существующие записи не удаляются и не перезаписываются."
            )
            await seed_bars(session)
            await seed_menu_if_empty(session)
            await seed_hub_content_if_empty(session)
            print(
                "Итог: "
                f"бары={await row_count(session, Bar)}, "
                f"категории={await row_count(session, Category)}, "
                f"блюда={await row_count(session, Dish)}, "
                f"мероприятия={await row_count(session, Event)}, "
                f"вакансии={await row_count(session, Vacancy)}, "
                f"лояльность={await row_count(session, LoyaltyInfo)}."
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

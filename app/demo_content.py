"""Illustrative Sprint 2 content, used only in explicit DEMO_MODE."""
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select

from app.db.model import Event, LoyaltyInfo, Vacancy


async def seed_demo_content(session):
    today = date.today()
    if await session.scalar(select(Event.id).limit(1)) is None:
        session.add_all([
            Event(
                title="Вечер сезонной кухни",
                description="Знакомимся с сезонными сочетаниями и блюдами из рыбы. В центре вечера — продукты, вкус и общение за одним столом.",
                starts_at=datetime.combine(
                    today + timedelta(days=3), time(19), tzinfo=UTC
                ),
                image_url="/assets/salmon.jpg",
                is_published=True,
            ),
            Event(
                title="Мастер-класс с шефом",
                description="Шеф расскажет о сочетаниях рыбы, овощей и соусов и покажет один из вариантов подачи. Подробности мероприятия уточняются.",
                starts_at=datetime.combine(
                    today + timedelta(days=10), time(18), tzinfo=UTC
                ),
                image_url="/assets/tartare.jpg",
                is_published=True,
            ),
            Event(
                title="Черновик мероприятия",
                description="Не должен показываться посетителю.",
                starts_at=datetime.combine(today, time(18), tzinfo=UTC),
                is_published=False,
            ),
        ])
    if await session.scalar(select(Vacancy.id).limit(1)) is None:
        session.add_all([
            Vacancy(
                title="Повар горячего цеха",
                description="Готовить блюда по технологическим картам, поддерживать порядок на рабочем месте и работать в команде кухни.\nОпыт работы на аналогичной позиции будет преимуществом.",
                salary="от 65 000 ₽ в месяц",
                is_published=True,
            ),
            Vacancy(
                title="Официант",
                description="Помогать гостям с выбором блюд, принимать заказы и поддерживать уютную атмосферу в зале.\nВажны внимательность и желание работать с людьми.",
                is_published=True,
            ),
            Vacancy(
                title="Бариста",
                description="Готовить кофе и другие напитки, следить за качеством подачи и чистотой рабочего места.",
                salary="Обсуждается на собеседовании",
                is_published=True,
            ),
            Vacancy(
                title="Черновик вакансии",
                description="Не должен показываться посетителю.",
                is_published=False,
            ),
        ])
    if await session.scalar(
        select(LoyaltyInfo.id).where(LoyaltyInfo.key == "loyalty")
    ) is None:
        session.add(
            LoyaltyInfo(
                key="loyalty",
                title="Программа лояльности",
                summary="Готовим больше приятных поводов возвращаться.",
                content=(
                    "Мы разрабатываем программу лояльности для гостей Рыбалтики.\n\n"
                    "Правила участия и доступные преимущества пока согласуются. "
                    "Когда условия будут утверждены, мы опубликуем их на этой странице.\n\n"
                    "Следите за обновлениями — вся актуальная информация появится здесь."
                ),
                is_published=True,
                version=1,
            )
        )
    await session.commit()

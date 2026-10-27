"""Illustrative Sprint 2 content, used only in explicit DEMO_MODE."""
from datetime import date, timedelta

from sqlalchemy import select

from app.db.content import Event, LoyaltyPage, Vacancy


async def seed_demo_content(session):
    # A saved (even unpublished) page is a marker: never overwrite an editor's work.
    if await session.get(LoyaltyPage, 1) is not None:
        return
    today = date.today()
    if await session.scalar(select(Event.id).limit(1)) is None:
        session.add_all([
            Event(title='Вечер сезонной кухни', description='Знакомимся с сезонными сочетаниями и блюдами из рыбы. В центре вечера — продукты, вкус и общение за одним столом.', event_date=today + timedelta(days=3), image_url='/assets/salmon.jpg', is_published=True),
            Event(title='Мастер-класс с шефом', description='Шеф расскажет о сочетаниях рыбы, овощей и соусов и покажет один из вариантов подачи. Подробности мероприятия уточняются.', event_date=today + timedelta(days=10), image_url='/assets/tartare.jpg', is_published=True),
            Event(title='Черновик мероприятия', description='Не должен показываться посетителю.', event_date=today, image_url=None, is_published=False),
        ])
    if await session.scalar(select(Vacancy.id).limit(1)) is None:
        session.add_all([
            Vacancy(position='Повар горячего цеха', description='Готовить блюда по технологическим картам, поддерживать порядок на рабочем месте и работать в команде кухни.\nОпыт работы на аналогичной позиции будет преимуществом.', salary='от 65 000 ₽ в месяц', is_published=True),
            Vacancy(position='Официант', description='Помогать гостям с выбором блюд, принимать заказы и поддерживать уютную атмосферу в зале.\nВажны внимательность и желание работать с людьми.', salary=None, is_published=True),
            Vacancy(position='Бариста', description='Готовить кофе и другие напитки, следить за качеством подачи и чистотой рабочего места.', salary='Обсуждается на собеседовании', is_published=True),
            Vacancy(position='Черновик вакансии', description='Не должен показываться посетителю.', salary=None, is_published=False),
        ])
    session.add(LoyaltyPage(id=1, title='Программа лояльности', summary='Готовим больше приятных поводов возвращаться.', body='Мы разрабатываем программу лояльности для гостей Рыбалтики.\n\nПравила участия и доступные преимущества пока согласуются. Когда условия будут утверждены, мы опубликуем их на этой странице.\n\nСледите за обновлениями — вся актуальная информация появится здесь.', is_published=True, version=1))
    await session.commit()

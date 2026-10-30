"""Explicit opt-in sample data; never seed the production database."""
from decimal import Decimal
from sqlalchemy import select
from app.db.model import Category, Dish

CATEGORIES = ['Рыба и морепродукты', 'Салаты', 'Супы', 'Десерты', 'Напитки']
# Photos illustrate the demonstration menu, not the restaurant's actual dishes.
DISHES = [
    (1, 'Лосось на гриле', 'Филе лосося, сезонные овощи, лимон, оливковое масло, зелень.', '890', 'salmon.jpg'),
    (1, 'Тартар из лосося', 'Лосось, авокадо, красная икра, базилик, лимон.', '720', 'tartare.jpg'),
    (1, 'Филе судака', 'Судак, картофельное пюре, сливки, зелень, лимон.', '690', None),
    (2, 'Овощной боул', 'Авокадо, томаты, нут, морковь, перец, капуста, салатные листья.', '450', 'salad.jpg'),
    (2, 'Зелёный салат', 'Салатные листья, огурец, зелень, лимонная заправка.', '320', 'salad.jpg'),
    (3, 'Уха по-домашнему', 'Судак, картофель, морковь, лук, укроп, рыбный бульон.', '390', None),
    (4, 'Ягодный десерт', 'Сливочный крем, бисквит, сезонные ягоды, сахар.', '360', None),
    (5, 'Домашний лимонад', 'Лимон, мята, сахарный сироп, газированная вода.', '220', None),
]

async def seed_demo(session):
    if await session.scalar(select(Category.id).limit(1)) is not None:
        return
    session.add_all(Category(id=i, name=name, sort_order=i) for i, name in enumerate(CATEGORIES, 1))
    await session.flush()
    for category_id, name, description, price, photo in DISHES:
        session.add(Dish(category_id=category_id, name=name, description=description,
                         price=Decimal(price), image_url=f'/assets/{photo}' if photo else None,
                         is_available=True))
    await session.commit()

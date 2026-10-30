from app.db.crud.base import CRUDBase
from app.db.crud.dish import DishCRUD
from app.db.crud.hub import (
    BarCRUD,
    EventCRUD,
    LoyaltyInfoCRUD,
    VacancyCRUD,
)
from app.db.model import Bar, Category, Dish, Event, LoyaltyInfo, Vacancy

bar_crud = BarCRUD(Bar)
category_crud = CRUDBase[Category](Category)
dish_crud = DishCRUD(Dish)
event_crud = EventCRUD(Event)
vacancy_crud = VacancyCRUD(Vacancy)
loyalty_info_crud = LoyaltyInfoCRUD(LoyaltyInfo)

__all__ = [
    "CRUDBase",
    "DishCRUD",
    "BarCRUD",
    "EventCRUD",
    "VacancyCRUD",
    "LoyaltyInfoCRUD",
    "bar_crud",
    "category_crud",
    "dish_crud",
    "event_crud",
    "vacancy_crud",
    "loyalty_info_crud",
]

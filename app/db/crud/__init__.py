from app.db.crud.base import CRUDBase
from app.db.crud.hub import BarCRUD, EventCRUD, LoyaltyInfoCRUD, VacancyCRUD
from app.db.model import Bar, Event, LoyaltyInfo, Vacancy

bar_crud = BarCRUD(Bar)
event_crud = EventCRUD(Event)
vacancy_crud = VacancyCRUD(Vacancy)
loyalty_info_crud = LoyaltyInfoCRUD(LoyaltyInfo)

__all__ = [
    "CRUDBase",
    "bar_crud",
    "event_crud",
    "vacancy_crud",
    "loyalty_info_crud",
]

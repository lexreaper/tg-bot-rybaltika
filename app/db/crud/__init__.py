from app.db.crud.base import CRUDBase
from app.db.crud.dish import DishCRUD
from app.db.model import Booking, Category, Dish, Review, User

user_crud = CRUDBase[User](User)
category_crud = CRUDBase[Category](Category)
dish_crud = DishCRUD(Dish)
booking_crud = CRUDBase[Booking](Booking)
review_crud = CRUDBase[Review](Review)

__all__ = [
    "CRUDBase",
    "DishCRUD",
    "user_crud",
    "category_crud",
    "dish_crud",
    "booking_crud",
    "review_crud",
]

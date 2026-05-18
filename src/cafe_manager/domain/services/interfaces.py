from typing import Protocol

from cafe_manager.domain.repository import OuterIDRepo

from ..entities.menu import Ingredient, MenuItem
from ..entities.order import Order
from ..entities.finance import Account, Money
from ..entities.people import Client
from ..entities.equipment import Table, Chair


class IDGenerator(Protocol):
    def generate_unique_code(
        self, obj_class: type, repo: OuterIDRepo, length: int = 6
    ) -> str: ...


class IngredientCalculator(Protocol):
    def calculate(
        self, menu_items: dict[MenuItem, int] | None
    ) -> dict[Ingredient, float]: ...


class PaymentService(Protocol):
    def process(
        self,
        order: Order,
        account: Account,
        client: Client | None,
        cash_provided: Money,
    ) -> tuple[Order, Account, Client | None]: ...


class SeatingService(Protocol):
    def reserve(
        self,
        tables: list[Table],
        free_chairs: list[Chair],
        people_amount: int,
    ) -> tuple[Table, list[Table], list[Chair]]: ...

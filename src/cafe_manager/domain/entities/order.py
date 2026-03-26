from datetime import datetime
from enum import StrEnum


from .menu import MenuItem
from .finance import Money
from cafe_manager.common.exceptions import (
    OrderIsEmptyError,
    OrderStateError,
    TableStateError,
)


class OrderState(StrEnum):
    AWAITING_PAYMENT = "awaiting-payment"
    PAID = "paid"
    IN_PROGRESS = "in-progress"
    READY = "ready"
    COMPLETED = "completed"


class Order:
    def __init__(
        self,
        order_id: str,
        items: dict[MenuItem, int],
        table_id: int | None = None,
        client_id: str | None = None,
        employee_id: str | None = None,
        machine_id: int | None = None,
        created_at: datetime | None = None,
        paid_at: datetime | None = None,
        total_price: Money | None = None,
        state: OrderState = OrderState.AWAITING_PAYMENT,
    ) -> None:
        self.order_id = order_id
        self._items = items

        self.table_id = table_id
        self.client_id = client_id
        self.employee_id = employee_id
        self.machine_id = machine_id

        self.created_at = created_at or datetime.now()
        self.paid_at = paid_at
        self.total_price = total_price or self._calculate_price(items)
        self._state = state

        if items == {}:
            raise OrderIsEmptyError(
                "Impossible to create order without any items from the menu"
            )

    def _calculate_price(self, items: dict[MenuItem, int] | None) -> Money:
        price = Money()
        if items:
            for item, amount in items.items():
                price += item.price * amount
        return price

    @property
    def items_amount(self) -> int:
        return len(self._items)

    @property
    def items(self) -> dict[MenuItem, int]:
        return dict(self._items)

    def pay(self) -> None:
        if self._state != OrderState.AWAITING_PAYMENT:
            raise OrderStateError(
                "Impossible to pay order in any state except 'AWAITING PAYMENT'"
            )

        self._state = OrderState.PAID
        self.paid_at = datetime.now()

    def start_cooking(self, employee_id: str) -> None:
        if self._state != OrderState.PAID:
            raise TableStateError(
                "Impossible to start cooking order in any state except 'PAID'"
            )

        self._state = OrderState.IN_PROGRESS
        self.employee_id = employee_id

    def end_cooking(self) -> None:
        if self._state != OrderState.IN_PROGRESS:
            raise OrderStateError(
                "Impossible to end cooking order in any state except 'IN PROGRESS'"
            )

        self._state = OrderState.READY
         
    def complete(self) -> None:
        if self._state != OrderState.READY:
            raise OrderStateError(
                "Impossible to complete order in any state except 'READY'"
            )

        self._state = OrderState.COMPLETED

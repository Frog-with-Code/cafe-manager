from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4


from .menu import MenuItem
from .finance import Money
from cafe_manager.common.exceptions import (
    OrderStateError,
    OrderModificationError,
    OrderPaymentError,
)


class OrderState(StrEnum):
    AWAITING_PAYMENT = "awaiting-payment"
    PAID = "paid"
    IN_PROGRESS = "in-progress"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order:
    def __init__(
        self,
        order_id: str,
        items: dict[MenuItem, int],
        client_id: str | None = None,
        table_id: int | None = None,
        created_at: datetime | None = None, 
        paid_at: datetime | None = None,
        total_price: Money | None = None,
        state: OrderState | None = OrderState.AWAITING_PAYMENT
    ) -> None:
        self.client_id = client_id
        self.order_id = order_id
        
        self.table_id = table_id
        self.employee_id = None
        self._items = items
        self.created_at = created_at or datetime.now()
        self.paid_at = paid_at
        self.total_price = total_price or self._calculate_price(items)
        self._state = state

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

    def add_item(self, item: MenuItem, amount: int) -> None:
        if self._state != OrderState.AWAITING_PAYMENT:
            raise OrderStateError("Order is already paid or cancelled")

        self._items[item] = self._items.get(item, 0) + amount
        self.total_price += item.price * amount

    def can_remove(self, item: MenuItem, amount: int) -> bool:
        if item not in self._items:
            return False
        if self._items[item] < amount:
            return False
        return True

    def remove_item(self, item: MenuItem, amount: int) -> None:
        if self._state != OrderState.AWAITING_PAYMENT:
            raise OrderStateError("Order is already paid or cancelled")

        if not self.can_remove(item, amount):
            raise OrderModificationError(f"There is not {amount} {item} in the order")
        self._items[item] -= amount
        self.total_price -= item.price * amount

    def can_be_paid(self) -> bool:
        if self._state != OrderState.AWAITING_PAYMENT:
            return False
        if len(self._items) <= 0:
            return False
        if self.total_price.amount == 0:
            return False
        return True

    def pay(self) -> None:
        if not self.can_be_paid():
            raise OrderPaymentError("Impossible to pay order due to inner properties")

        self._state = OrderState.PAID
        self.paid_at = datetime.now()

    def start_cooking(self, employee_id: str) -> None:
        match (self._state):
            case OrderState.AWAITING_PAYMENT:
                raise OrderStateError("Order is not paid")
            case OrderState.PAID:
                self._state = OrderState.IN_PROGRESS
                self.employee_id = employee_id
            case _:
                raise OrderStateError("Order is already cooked or cancelled")

    def end_cooking(self) -> None:
        if self._state != OrderState.IN_PROGRESS:
            raise OrderStateError("Order is not cooking")

        self._state = OrderState.READY

    def cancel(self) -> None:
        match (self._state):
            case OrderState.AWAITING_PAYMENT:
                self._state = OrderState.CANCELLED
            case _:
                raise OrderStateError("Impossible to cancel paid order")

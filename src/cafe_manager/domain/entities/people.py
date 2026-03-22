from datetime import datetime
from enum import StrEnum
from cafe_manager.common.exceptions import EmployeeStateError
from cafe_manager.domain.entities.finance import Money


class EmployeeState(StrEnum):
    FREE = "free"
    BUSY = "busy"


class Employee:
    def __init__(
        self,
        name: str,
        employee_id: str,
        state: EmployeeState = EmployeeState.FREE,
        rest_start: datetime | None = None,
    ) -> None:
        self.name = name
        self.employee_id = employee_id
        self._state = state
        self.rest_start = rest_start or datetime.now()

    def can_work(self) -> bool:
        return self._state == EmployeeState.FREE

    def work(self) -> None:
        if not self.can_work():
            raise EmployeeStateError("Employee is not free")
        self._state = EmployeeState.BUSY

    def rest(self) -> None:
        match (self._state):
            case EmployeeState.FREE:
                print("Employee is already resting")
            case EmployeeState.BUSY:
                self.rest_start = datetime.now()
                self._state = EmployeeState.FREE
                print("Employee is free now")
            case _:
                raise EmployeeStateError("Unknown state")


class Client:
    def __init__(
        self,
        client_id: str,
        name: str,
        total_spent: Money = Money(),
        orders_amount: int = 0,
        registered_at: datetime | None = None,
    ):
        self.client_id = client_id
        self.name = name
        self.total_spent = total_spent
        self.orders_amount = orders_amount
        self.registered_at = registered_at or datetime.now()

    def pay(self, order_price: Money) -> None:
        self.total_spent = order_price
        self.orders_amount += 1

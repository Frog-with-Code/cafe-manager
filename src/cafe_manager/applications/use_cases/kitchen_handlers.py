from cafe_manager.domain.entities.order import Order
from cafe_manager.infrastructure.interfaces import EmployeeRepo, OrderRepo
from cafe_manager.common.exceptions import (
    EmployeeNotFoundError,
    KitchenOverloadError,
    OrderNotFoundError,
)


class KitchenStartHandler:
    def __init__(self, order_repo: OrderRepo, employee_repo: EmployeeRepo) -> None:
        self._order_repo = order_repo
        self._employee_repo = employee_repo

    def handle(self, employee_id: str | None) -> str | None:
        employee = (
            self._employee_repo.get_by_id(employee_id)
            if employee_id
            else self._employee_repo.get_most_free()
        )
        order = self._order_repo.get_oldest_paid()

        if order is None:
            return None

        if employee is None:
            if employee_id is None:
                raise KitchenOverloadError("All employees are busy")
            else:
                raise EmployeeNotFoundError(
                    f"Employee with ID {employee_id} was not found"
                )

        employee.work()
        order.start_cooking(employee.employee_id)

        self._order_repo.save(order)
        self._employee_repo.save(employee)
        return order.order_id


class KitchenListPending:
    def __init__(self, order_repo: OrderRepo) -> None:
        self._order_repo = order_repo

    def handle(self) -> list[Order]:
        paid_orders = self._order_repo.get_paid_from_oldest()

        return paid_orders if paid_orders else []


class KitchenReadyHandler:
    def __init__(self, order_repo: OrderRepo) -> None:
        self._order_repo = order_repo

    def handle(self, order_id: str) -> None:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order with ID {order_id} was not found")
    
        order.end_cooking()

        self._order_repo.save(order)

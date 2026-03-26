from cafe_manager.domain.entities.equipment import CoffeeMachine
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.entities.people import Employee
from cafe_manager.domain.services import IngredientCalculator

from cafe_manager.application.interfaces import (
    CoffeeMachineRepo,
    EmployeeRepo,
    InventoryRepo,
    OrderRepo,
)

from cafe_manager.common.exceptions import (
    CoffeeMachineNotFoundError,
    EmployeeNotFoundError,
    KitchenOverloadError,
    OrderNotFoundError,
)


class KitchenStartHandler:
    def __init__(
        self,
        order_repo: OrderRepo,
        employee_repo: EmployeeRepo,
        inventory_repo: InventoryRepo,
        machine_repo: CoffeeMachineRepo,
        ingredient_calculator: IngredientCalculator,
    ) -> None:
        self._order_repo = order_repo
        self._employee_repo = employee_repo
        self._inventory_repo = inventory_repo
        self._machine_repo = machine_repo

        self._ingredient_calculator = ingredient_calculator

    def _start_coffee_machine(self, order: Order) -> tuple[CoffeeMachine | None, Order]:
        needs_coffee_machine = any(
            item.requires_coffee_machine for item in order.items.keys()
        )

        machine = None
        if needs_coffee_machine:
            machine = self._machine_repo.get_free()
            if machine is None:
                raise KitchenOverloadError("All coffee-machines are busy")

            machine.start()
            order.machine_id = machine.machine_id

        return machine, order

    def _get_employee(self, employee_id: str | None) -> Employee:
        employee = (
            self._employee_repo.get_by_id(employee_id)
            if employee_id
            else self._employee_repo.get_most_free()
        )

        if employee is None:
            if employee_id is None:
                raise KitchenOverloadError("All employees are busy")
            else:
                raise EmployeeNotFoundError(
                    f"Employee with ID {employee_id} was not found"
                )

        return employee

    def handle(
        self, employee_id: str | None
    ) -> tuple[str, str | None, int | None] | tuple[None, ...]:
        order = self._order_repo.get_oldest_paid()

        if order is None:
            return (None,) * 3

        employee = self._get_employee(employee_id)

        menu_items = order.items
        required_ingredients = self._ingredient_calculator.calculate(menu_items)

        employee.work()
        order.start_cooking(employee.employee_id)

        machine, order = self._start_coffee_machine(order)

        if machine is not None:
            self._machine_repo.save(machine)
        self._inventory_repo.withdraw(required_ingredients)
        self._order_repo.save(order)
        self._employee_repo.save(employee)

        return order.order_id, order.employee_id, order.machine_id


class KitchenListPending:
    def __init__(self, order_repo: OrderRepo) -> None:
        self._order_repo = order_repo

    def handle(self) -> list[Order]:
        paid_orders = self._order_repo.get_paid_from_oldest()

        return paid_orders if paid_orders else []


class KitchenReadyHandler:
    def __init__(self, order_repo: OrderRepo, machine_repo: CoffeeMachineRepo) -> None:
        self._order_repo = order_repo
        self._machine_repo = machine_repo

    def _stop_coffee_machine(self, machine_id: int | None) -> CoffeeMachine | None:
        machine = None
        if machine_id:
            machine = self._machine_repo.get_by_id(machine_id)
            if machine is None:
                raise CoffeeMachineNotFoundError(
                    f"Coffee-machine with ID {machine_id} was not found"
                )
            machine.stop()

        return machine

    def handle(self, order_id: str) -> None:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order with ID {order_id} was not found")

        order.end_cooking()

        machine = self._stop_coffee_machine(order.machine_id)

        self._order_repo.save(order)
        if machine:
            self._machine_repo.save(machine)

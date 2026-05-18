from cafe_manager.domain.entities.equipment import CoffeeMachine
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.entities.people import Employee
from cafe_manager.domain.services.interfaces import IngredientCalculator

from cafe_manager.application.uow import UnitOfWork

from cafe_manager.common.exceptions import (
    CoffeeMachineNotFoundError,
    EmployeeNotFoundError,
    KitchenOverloadError,
    OrderNotFoundError,
)


class KitchenStartHandler:
    def __init__(self, uow: UnitOfWork, ingredient_calculator: IngredientCalculator):
        self._uow = uow
        self._ingredient_calculator = ingredient_calculator

    def _start_coffee_machine(
        self, uow: UnitOfWork, order: Order
    ) -> tuple[CoffeeMachine | None, Order]:
        needs_coffee_machine = any(
            item.requires_coffee_machine for item in order.items.keys()
        )

        machine = None
        if needs_coffee_machine:
            machine = uow.machine_repo.get_free()
            if machine is None:
                raise KitchenOverloadError("All coffee-machines are busy")

            machine.start()
            order.machine_id = machine.machine_id

        return machine, order

    def _get_employee(self, uow: UnitOfWork, employee_id: str | None) -> Employee:
        employee = (
            uow.employee_repo.get_by_id(employee_id)
            if employee_id
            else uow.employee_repo.get_most_free()
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
        with self._uow as uow:
            order = uow.order_repo.get_oldest_paid()

            if order is None:
                return (None,) * 3

            employee = self._get_employee(uow, employee_id)

            menu_items = order.items
            required_ingredients = self._ingredient_calculator.calculate(menu_items)

            employee.work()
            order.start_cooking(employee.employee_id)

            machine, order = self._start_coffee_machine(uow, order)

            if machine is not None:
                uow.machine_repo.save(machine)
            uow.inventory_repo.withdraw(required_ingredients)
            uow.order_repo.save(order)
            uow.employee_repo.save(employee)

            return order.order_id, order.employee_id, order.machine_id


class KitchenListPending:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self) -> list[Order]:
        with self._uow as uow:
            paid_orders = uow.order_repo.get_paid_from_oldest()
            return paid_orders if paid_orders else []


class KitchenReadyHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def _stop_coffee_machine(
        self, uow: UnitOfWork, machine_id: int | None
    ) -> CoffeeMachine | None:
        machine = None
        if machine_id:
            machine = uow.machine_repo.get_by_id(machine_id)
            if machine is None:
                raise CoffeeMachineNotFoundError(
                    f"Coffee-machine with ID {machine_id} was not found"
                )
            machine.stop()

        return machine

    def handle(self, order_id: str) -> None:
        with self._uow as uow:
            order = uow.order_repo.get_by_id(order_id)
            if order is None:
                raise OrderNotFoundError(f"Order with ID {order_id} was not found")

            order.end_cooking()

            machine = self._stop_coffee_machine(uow, order.machine_id)

            uow.order_repo.save(order)
            if machine:
                uow.machine_repo.save(machine)

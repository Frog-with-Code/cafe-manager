from uuid import UUID

from cafe_manager.domain.entities.equipment import (
    Chair,
    Table,
    TableState,
)
from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import Ingredient, MenuItem
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.services.interfaces import (
    IDGenerator,
    IngredientCalculator,
    PaymentService,
)

from cafe_manager.application.uow import UnitOfWork

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ClientNotFoundError,
    EmployeeNotAssignedError,
    EmployeeNotFoundError,
    IngredientNotFoundError,
    InsufficientStocksError,
    MenuItemNotFoundError,
    MenuItemRepeatError,
    OrderNotFoundError,
    TableNotFoundError,
    TableStateError,
)


class OrderCreateHandler:
    def __init__(
        self,
        uow: UnitOfWork,
        ingredient_calculator: IngredientCalculator,
        id_generator: IDGenerator,
    ) -> None:
        self._uow = uow
        self._ingredient_calculator = ingredient_calculator
        self._id_generator = id_generator

    def _resolve_items(
        self, uow: UnitOfWork, ordered: list[tuple[str, int]]
    ) -> dict[MenuItem, int]:
        items = {}
        for item_name, amount in ordered:
            item = uow.menu_repo.get_by_name(item_name)

            if item is None:
                raise MenuItemNotFoundError(
                    f"Menu item with name '{item_name}' was not found"
                )
            if items.get(item) is not None:
                raise MenuItemRepeatError(
                    f"Several menu items with name '{item_name}' was provided"
                )

            items[item] = amount

        return items

    def _occupy_table(
        self, uow: UnitOfWork, table_id: int, continue_session: bool
    ) -> tuple[Table, list[Chair]]:
        table = uow.table_repo.get_by_id(table_id)

        if table is None:
            raise TableNotFoundError(f"Table with ID {table} was not found")
        chairs = uow.chair_repo.get_busy_by_table_id(table_id) or []

        if continue_session:
            if table._state != TableState.OCCUPIED:
                raise TableStateError(
                    "Table is not occupied. Session can't be continued"
                )
        else:
            table.occupy()
            for chair in chairs:
                chair.occupy()

        return table, chairs

    def _check_ingredients(
        self, uow: UnitOfWork, ingredients_required: dict[Ingredient, float]
    ) -> None:
        for ingredient, amount in ingredients_required.items():
            name = ingredient.name
            free_amount = uow.inventory_repo.get_free_by_name(name)

            if free_amount is None:
                raise IngredientNotFoundError(f"No '{name}' in the inventory")

            if free_amount < amount:
                raise InsufficientStocksError(
                    f"Not enough '{name}' supplies. {amount} is required, {free_amount} in stock"
                )

    def handle(
        self,
        ordered: list[tuple[str, int]],
        table_id: int | None,
        continue_session: bool,
    ) -> str:
        with self._uow as uow:
            items = self._resolve_items(uow, ordered)
            ingredients_required = self._ingredient_calculator.calculate(items)

            table: Table | None = None
            chairs: list[Chair] = []
            if table_id is not None:
                table, chairs = self._occupy_table(uow, table_id, continue_session)

            self._check_ingredients(uow, ingredients_required)

            generated_id = self._id_generator.generate_unique_code(
                Order, uow.order_repo
            )
            order = Order(order_id=generated_id, items=items, table_id=table_id)

            uow.order_repo.save(order)
            uow.inventory_repo.reserve(ingredients_required)
            if table_id is not None:
                uow.table_repo.save(table)  # type: ignore[arg-type]
                uow.chair_repo.save_many(chairs)  # type: ignore[arg-type]

            return order.order_id


class OrderPayHandler:
    def __init__(self, uow: UnitOfWork, payment_service: PaymentService) -> None:
        self._uow = uow
        self._payment_service = payment_service

    def handle(
        self,
        order_id: str,
        cash_provided: Money,
        account_id: UUID | None,
        client_id: str | None,
    ) -> None:
        with self._uow as uow:
            order = uow.order_repo.get_by_id(order_id)
            if order is None:
                raise OrderNotFoundError(f"Order with ID {order_id} was not found")

            account = (
                uow.finance_repo.get_by_id(account_id)
                if account_id
                else uow.finance_repo.get_primary()
            )
            if account is None:
                raise AccountNotFoundError(
                    f"Account with ID {account_id} was not found"
                )

            client = None
            if client_id is not None:
                client = uow.client_repo.get_by_id(client_id)
                if client is None:
                    raise ClientNotFoundError(
                        f"Client with ID {client_id} was not found"
                    )

            u_order, u_account, u_client = self._payment_service.process(
                order=order,
                account=account,
                client=client,
                cash_provided=cash_provided,
            )

            uow.order_repo.save(u_order)
            uow.finance_repo.save(u_account)
            if u_client:
                uow.client_repo.save(u_client)


class OrderServeHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, order_id: str) -> None:
        with self._uow as uow:
            order = uow.order_repo.get_by_id(order_id)
            if order is None:
                raise OrderNotFoundError(f"Order with ID {order_id} was not found")

            order.complete()

            if order.employee_id is None:
                raise EmployeeNotAssignedError("Employee not assigned to the order")

            employee = uow.employee_repo.get_by_id(order.employee_id)
            if employee is None:
                raise EmployeeNotFoundError(
                    f"Employee with ID {order.employee_id} was not found"
                )

            employee.rest()

            uow.order_repo.save(order)
            uow.employee_repo.save(employee)


class OrderInfoHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self) -> list[Order]:
        with self._uow as uow:
            orders = uow.order_repo.get_all_active()

            return orders or []


class OrderShowItemsHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, order_id: str) -> dict[MenuItem, int]:
        with self._uow as uow:
            order = uow.order_repo.get_by_id(order_id)
            if order is None:
                raise OrderNotFoundError(f"Order with ID '{order_id}' was not found")

            return order.items

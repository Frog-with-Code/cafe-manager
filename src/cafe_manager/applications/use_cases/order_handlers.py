from uuid import UUID
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
from cafe_manager.domain.entities.equipment import Chair, Table, TableState
from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import Ingredient, MenuItem
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.domain.services.ingredient_calculator import IngredientCalculator
from cafe_manager.domain.services.payment_service import PaymentService
from cafe_manager.infrastructure.interfaces import (
    ChairRepo,
    ClientRepo,
    EmployeeRepo,
    FinanceRepo,
    InventoryRepo,
    MenuRepo,
    OrderRepo,
    TableRepo,
)


class OrderCreateHandler:
    def __init__(
        self,
        order_repo: OrderRepo,
        inventory_repo: InventoryRepo,
        menu_repo: MenuRepo,
        table_repo: TableRepo,
        chair_repo: ChairRepo,
        ingredient_calculator: IngredientCalculator,
        id_generator: IDGeneratingService,
    ) -> None:
        self._order_repo = order_repo
        self._inventory_repo = inventory_repo
        self._menu_repo = menu_repo
        self._table_repo = table_repo
        self._chair_repo = chair_repo

        self._ingredient_calculator = ingredient_calculator
        self._id_generator = id_generator

    def _resolve_items(self, ordered: list[tuple[str, int]]) -> dict[MenuItem, int]:
        items = {}
        for item_name, amount in ordered:
            item = self._menu_repo.get_by_name(item_name)

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
        self, table_id: int, continue_session: bool
    ) -> tuple[Table, list[Chair]]:
        table = self._table_repo.get_by_id(table_id)

        if table is None:
            raise TableNotFoundError(f"Table with ID {table} was not found")
        chairs = self._chair_repo.get_busy_by_table_id(table_id) or []

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

    def _generate_id(self) -> str:
        while True:
            generated_id = self._id_generator.generate_unique_code(Order)

            if self._order_repo.get_by_id(generated_id) is None:
                break

        return generated_id

    def _check_ingredients(self, ingredients_required: dict[Ingredient, float]) -> None:
        for ingredient, amount in ingredients_required.items():
            name = ingredient.name
            free_amount = self._inventory_repo.get_free_by_name(name)

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
        items = self._resolve_items(ordered)
        ingredients_required = self._ingredient_calculator.calculate(items)

        if table_id is not None:
            table, chairs = self._occupy_table(table_id, continue_session)

        generated_id = self._generate_id()
        order = Order(order_id=generated_id, items=items, table_id=table_id)

        self._order_repo.save(order)
        self._inventory_repo.reserve(ingredients_required)
        if table_id is not None:
            self._table_repo.save(table)  # type: ignore
            self._chair_repo.save_many(chairs)  # type: ignore

        return order.order_id


class OrderPayHandler:
    def __init__(
        self,
        order_repo: OrderRepo,
        finance_repo: FinanceRepo,
        client_repo: ClientRepo,
        payment_service: PaymentService,
    ) -> None:
        self._order_repo = order_repo
        self._finance_repo = finance_repo
        self._client_repo = client_repo

        self._payment_service = payment_service

    def handle(
        self,
        order_id: str,
        cash_provided: Money,
        account_id: UUID | None,
        client_id: str | None,
    ) -> None:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order with ID {order_id} was not found")

        account = (
            self._finance_repo.get_by_id(account_id)
            if account_id
            else self._finance_repo.get_primary()
        )
        if account is None:
            raise AccountNotFoundError(f"Account with ID {account_id} was not found")

        client = None
        if client_id is not None:
            client = self._client_repo.get_by_id(client_id)
            if client is None:
                raise ClientNotFoundError(f"Client with ID {client_id} was not found")

        u_order, u_account, u_client = self._payment_service.process(
            order=order, account=account, client=client, cash_provided=cash_provided
        )

        self._order_repo.save(u_order)
        self._finance_repo.save(u_account)
        if u_client:
            self._client_repo.save(u_client)


class OrderServeHandler:
    def __init__(self, order_repo: OrderRepo, employee_repo: EmployeeRepo) -> None:
        self._order_repo = order_repo
        self._employee_repo = employee_repo

    def handle(self, order_id: str) -> None:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Order with ID {order_id} was not found")

        if order.employee_id is None:
            raise EmployeeNotAssignedError("Employee not assigned to the order")

        employee = self._employee_repo.get_by_id(order.employee_id)
        if employee is None:
            raise EmployeeNotFoundError(
                f"Employee with ID {order.employee_id} was not found"
            )

        order.end_cooking()
        employee.rest()

        self._order_repo.save(order)
        self._employee_repo.save(employee)


class OrderInfoHandler:
    def __init__(self, order_repo: OrderRepo) -> None:
        self._order_repo = order_repo

    def handle(self) -> list[Order]:
        orders = self._order_repo.get_all_active()

        return orders or []

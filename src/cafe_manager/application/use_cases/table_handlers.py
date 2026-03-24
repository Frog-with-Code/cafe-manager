from uuid import UUID

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ChairNotFoundError,
    InsufficientBudgetError,
    TableBusyError,
    TableNotFoundError,
    TablePlacesError,
)
from cafe_manager.domain.entities.equipment import Table
from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.services.seating_service import SeatingService
from cafe_manager.application.interfaces import (
    ChairRepo,
    FinanceRepo,
    OrderRepo,
    TableRepo,
)


class TableBuyHandler:
    def __init__(self, finance_repo: FinanceRepo, table_repo: TableRepo) -> None:
        self._finance_repo = finance_repo
        self._table_repo = table_repo

    def handle(self, price: Money, seats: int, account_id: UUID | None) -> None:
        account = (
            self._finance_repo.get_by_id(account_id)
            if account_id
            else self._finance_repo.get_primary()
        )
        if account is None:
            raise AccountNotFoundError(f"Account was not found")

        if account.balance < price:
            raise InsufficientBudgetError(
                f"Not enough money to buy chair for {str(price)}"
            )

        account.add_expense(price, f"Buy {seats}-seats table")
        table = Table(seats)

        self._finance_repo.save(account)
        self._table_repo.save(table)


class TableDiscardHandler:
    def __init__(self, table_repo: TableRepo, chair_repo: ChairRepo) -> None:
        self._table_repo = table_repo
        self._chair_repo = chair_repo

    def handle(self, table_id: int) -> None:
        if self._table_repo.get_by_id(table_id) is None:
            raise TableNotFoundError(f"Table with id {table_id} was not found")

        self._table_repo.delete_by_id(table_id)
        self._chair_repo.delete_table_by_id(table_id)


class TableInfoHandler:
    def __init__(self, table_repo: TableRepo) -> None:
        self._table_repo = table_repo

    def handle(self) -> list[Table]:
        tables = self._table_repo.get_all()
        return tables if tables else []


class TableReserveHandler:
    def __init__(
        self,
        table_repo: TableRepo,
        chair_repo: ChairRepo,
        seating_service: SeatingService,
    ) -> None:
        self._table_repo = table_repo
        self._chair_repo = chair_repo
        self._seating_service = seating_service

    def handle(self, seats_required: int) -> int:
        tables = self._table_repo.get_all()
        free_chairs = self._chair_repo.get_free()

        if not tables:
            raise TableNotFoundError("Impossible to reserve. No table found")
        if not free_chairs:
            raise ChairNotFoundError("Impossible to reserve. No free chairs found")

        reserved_table, modified_tables, modified_chairs = (
            self._seating_service.reserve(tables, free_chairs, seats_required)
        )

        self._table_repo.save_many(modified_tables)
        self._chair_repo.save_many(modified_chairs)
        return reserved_table.table_id or -1


class AssignChairToTableHandler:
    def __init__(self, table_repo: TableRepo, chair_repo: ChairRepo) -> None:
        self._table_repo = table_repo
        self._chair_repo = chair_repo

    def handle(self, table_id: int, chair_id: int) -> None:
        target_table = self._table_repo.get_by_id(table_id)
        chair = self._chair_repo.get_by_id(chair_id)

        if target_table is None:
            raise TableNotFoundError(f"Table with ID '{table_id}' was not found")
        if chair is None:
            raise ChairNotFoundError(f"Chair with ID '{chair_id}' was not found")

        prev_id = chair._table_id
        prev_table = self._table_repo.get_by_id(prev_id) if prev_id else None
        if prev_id is not None and prev_table is None:
            raise TableNotFoundError(f"Table with ID '{table_id}' was not found")

        if target_table.table_id == prev_id:
            return

        try:
            if prev_table:
                prev_table.remove_chair(chair_id)
            target_table.add_chair(chair_id)
            chair.assign_to_table(table_id)
        except TablePlacesError:
            raise

        self._table_repo.save(target_table)
        self._chair_repo.save(chair)
        if prev_table:
            self._table_repo.save(prev_table)


class TableFreeHandler:
    def __init__(
        self, table_repo: TableRepo, chair_repo: ChairRepo, order_repo: OrderRepo
    ) -> None:
        self._table_repo = table_repo
        self._chair_repo = chair_repo
        self._order_repo = order_repo

    def handle(self, table_id: int) -> None:
        table = self._table_repo.get_by_id(table_id)
        if table is None:
            raise TableNotFoundError(f"Table with id {table_id} was not found")

        orders = self._order_repo.get_active_by_table_id(table_id)
        if orders is not None:
            raise TableBusyError("Impossible to free table with active orders")

        chairs = self._chair_repo.get_busy_by_table_id(table_id)

        table.free()
        for chair in chairs or []:
            chair.free()

from uuid import UUID

from cafe_manager.domain.entities.equipment import Chair, Table, TableState
from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.services.interfaces import SeatingService

from cafe_manager.application.uow import UnitOfWork

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ChairNotFoundError,
    InsufficientBudgetError,
    TableBusyError,
    TableNotFoundError,
    TablePlacesError,
    TableStateError,
)


class TableBuyHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, price: Money, seats: int, account_id: UUID | None) -> None:
        with self._uow as uow:
            account = (
                uow.finance_repo.get_by_id(account_id)
                if account_id
                else uow.finance_repo.get_primary()
            )
            if account is None:
                raise AccountNotFoundError(f"Account was not found")

            if account.balance < price:
                raise InsufficientBudgetError(
                    f"Not enough money to buy table for {str(price)}"
                )

            account.add_expense(price, f"Buy {seats}-seats table")
            table = Table(seats)

            uow.finance_repo.save(account)
            uow.table_repo.save(table)


class TableDiscardHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, table_id: int) -> None:
        with self._uow as uow:
            table = uow.table_repo.get_by_id(table_id)
            if table is None:
                raise TableNotFoundError(f"Table with id {table_id} was not found")
            if table._state == TableState.OCCUPIED:
                raise TableStateError("Impossible to discard occupied table")

            uow.table_repo.delete_by_id(table_id)
            uow.chair_repo.delete_table_by_id(table_id)


class TableInfoHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self) -> list[Table]:
        with self._uow as uow:
            tables = uow.table_repo.get_all()
            return tables if tables else []


class TableReserveHandler:
    def __init__(self, uow: UnitOfWork, seating_service: SeatingService) -> None:
        self._uow = uow
        self._seating_service = seating_service

    def handle(self, seats_required: int) -> int:
        with self._uow as uow:
            tables = uow.table_repo.get_all()
            free_chairs = uow.chair_repo.get_free()

            if not tables:
                raise TableNotFoundError("Impossible to reserve. No table found")
            if not free_chairs:
                raise ChairNotFoundError("Impossible to reserve. No free chairs found")

            reserved_table, modified_tables, modified_chairs = (
                self._seating_service.reserve(tables, free_chairs, seats_required)
            )

            uow.table_repo.save_many(modified_tables)
            uow.chair_repo.save_many(modified_chairs)

            return reserved_table.table_id or -1


class AssignChairToTableHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def _get_entities(
        self, uow: UnitOfWork, table_id: int, chair_id: int
    ) -> tuple[Table, Chair, Table | None]:
        target_table = uow.table_repo.get_by_id(table_id)
        chair = uow.chair_repo.get_by_id(chair_id)

        if target_table is None:
            raise TableNotFoundError(f"Table with ID '{table_id}' was not found")
        if chair is None:
            raise ChairNotFoundError(f"Chair with ID '{chair_id}' was not found")

        prev_id = chair._table_id
        prev_table = uow.table_repo.get_by_id(prev_id) if prev_id else None
        if prev_id is not None and prev_table is None:
            raise TableNotFoundError(f"Table with ID '{table_id}' was not found")

        return target_table, chair, prev_table

    def _move_chair(
        self, target_table: Table, chair: Chair, prev_table: Table | None
    ) -> None:
        if target_table.table_id == chair._table_id:
            return

        try:
            if prev_table:
                prev_table.remove_chair(chair.chair_id)
            target_table.add_chair(chair.chair_id)
            chair.assign_to_table(target_table.table_id)
        except TablePlacesError:
            raise

    def handle(self, table_id: int, chair_id: int) -> None:
        with self._uow as uow:
            target_table, chair, prev_table = self._get_entities(
                uow, table_id, chair_id
            )

            self._move_chair(target_table, chair, prev_table)

            uow.table_repo.save(target_table)
            uow.chair_repo.save(chair)
            if prev_table:
                uow.table_repo.save(prev_table)


class TableFreeHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def _get_entities(
        self, uow: UnitOfWork, table_id: int
    ) -> tuple[Table, list[Chair]]:
        table = uow.table_repo.get_by_id(table_id)
        if table is None:
            raise TableNotFoundError(f"Table with id {table_id} was not found")

        orders = uow.order_repo.get_active_by_table_id(table_id)
        if orders is not None:
            raise TableBusyError("Impossible to free table with active orders")

        chairs = uow.chair_repo.get_busy_by_table_id(table_id) or []

        return table, chairs

    def handle(self, table_id: int) -> None:
        with self._uow as uow:
            table, chairs = self._get_entities(uow, table_id)

            table.free()
            for chair in chairs:
                chair.free()

            uow.table_repo.save(table)
            uow.chair_repo.save_many(chairs)

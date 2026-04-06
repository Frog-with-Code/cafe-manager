from uuid import UUID

from cafe_manager.domain.entities.equipment import Chair
from cafe_manager.domain.entities.finance import Money

from cafe_manager.application.interfaces import UnitOfWork

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ChairNotFoundError,
    InsufficientBudgetError,
    TableNotFoundError,
)


class ChairBuyHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, price: Money, account_id: UUID | None) -> None:
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
                    f"Not enough money to buy chair for {str(price)}"
                )

            account.add_expense(price, f"Buy chair")
            chair = Chair()

            uow.finance_repo.save(account)
            uow.chair_repo.save(chair)


class ChairDiscardHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, chair_id: int) -> None:
        with self._uow as uow:
            chair = uow.chair_repo.get_by_id(chair_id)
            if chair is None:
                raise ChairNotFoundError(f"Chair with id {chair_id} was not found")

            table_id = chair._table_id
            table = uow.table_repo.get_by_id(table_id) if table_id else None
            if table_id is not None and table is None:
                raise TableNotFoundError(f"Table with id {table_id} was not found")

            if table:
                table.remove_chair(chair_id)
                uow.table_repo.save(table)
            uow.chair_repo.delete_by_id(chair_id)


class ChairInfoHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self) -> list[Chair]:
        with self._uow as uow:
            chairs = uow.chair_repo.get_all()
            return chairs if chairs else []

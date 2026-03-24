from uuid import UUID

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ChairNotFoundError,
    InsufficientBudgetError,
    TableNotFoundError,
)
from cafe_manager.domain.entities.equipment import Chair
from cafe_manager.domain.entities.finance import Money
from cafe_manager.application.interfaces import ChairRepo, FinanceRepo, TableRepo


class ChairBuyHandler:
    def __init__(self, finance_repo: FinanceRepo, chair_repo: ChairRepo) -> None:
        self._finance_repo = finance_repo
        self._chair_repo = chair_repo

    def handle(self, price: Money, account_id: UUID | None) -> None:
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

        account.add_expense(price, f"Buy chair")
        chair = Chair()

        self._finance_repo.save(account)
        self._chair_repo.save(chair)


class ChairDiscardHandler:
    def __init__(self, chair_repo: ChairRepo, table_repo: TableRepo) -> None:
        self._chair_repo = chair_repo
        self._table_repo = table_repo

    def handle(self, chair_id: int) -> None:
        chair = self._chair_repo.get_by_id(chair_id)
        if chair is None:
            raise ChairNotFoundError(f"Table with id {chair_id} was not found")

        table_id = chair._table_id
        table = self._table_repo.get_by_id(table_id) if table_id else None
        if table_id is not None and table is None:
            raise TableNotFoundError(f"Table with id {table_id} was not found")

        if table:
            table.remove_chair(chair_id)
            self._table_repo.save(table)
        self._chair_repo.delete_by_id(chair_id)


class ChairInfoHandler:
    def __init__(self, chair_repo: ChairRepo) -> None:
        self._chair_repo = chair_repo

    def handle(self) -> list[Chair]:
        chairs = self._chair_repo.get_all()
        return chairs if chairs else []

from typing import Any
from uuid import UUID
from datetime import datetime
from cafe_manager.common.exceptions import AccountNotFoundError, RecordNotUpdatedError
from cafe_manager.domain.entities.finance import Money, Transaction, TransactionType
from cafe_manager.infrastructure.interfaces import FinanceRepo


class FinanceInvestHandler:
    def __init__(self, finance_repo: FinanceRepo) -> None:
        self._finance_repo = finance_repo

    def handle(self, amount: Money, account_id: UUID | None, message: str) -> None:
        account = (
            self._finance_repo.get_by_id(account_id)
            if account_id
            else self._finance_repo.get_primary()
        )
        if account is None:
            raise AccountNotFoundError("Account was not found")

        account.add_income(amount, message)
        self._finance_repo.save(account)


class FinanceStatsHandler:
    def __init__(self, finance_repo: FinanceRepo) -> None:
        self._finance_repo = finance_repo

    def handle(
        self,
        account_id: UUID | None,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> dict[str, Any]:
        account = (
            self._finance_repo.get_by_id(account_id)
            if account_id
            else self._finance_repo.get_primary()
        )
        if account is None:
            raise AccountNotFoundError("Account was not found")

        history = self._finance_repo.get_transactions_by_period(
            account.account_id, start_date, end_date
        )
        total_income = Money()
        total_expense = Money()

        if history:
            for t in history:
                if t.transaction_type == TransactionType.INCOME:
                    total_income += t.money
                if t.transaction_type == TransactionType.EXPENSE:
                    total_expense += t.money

        profit_raw = total_income.amount - total_expense.amount

        return {
            "id": account.account_id,
            "balance": account.balance,
            "income": total_income,
            "expense": total_expense,
            "profit_abs": Money(abs(profit_raw)),
            "is_loss": profit_raw < 0,
        }


class FinanceHistoryHandler:
    def __init__(self, finance_repo: FinanceRepo) -> None:
        self._finance_repo = finance_repo

    def handle(self, account_id: UUID | None, limit: int) -> list[Transaction]:
        account = (
            self._finance_repo.get_by_id(account_id)
            if account_id
            else self._finance_repo.get_primary()
        )

        if account is None:
            raise AccountNotFoundError(f"Account with ID {account_id} was not found")

        history = self._finance_repo.get_latest_transactions(account.account_id, limit)
        return history or []


class FinanceSetPrimaryHandler:
    def __init__(self, finance_repo: FinanceRepo) -> None:
        self._finance_repo = finance_repo

    def handle(self, account_id: UUID) -> None:
        try:
            self._finance_repo.set_primary(account_id)
        except RecordNotUpdatedError as e:
            raise AccountNotFoundError(
                f"Account with ID {account_id} was not found"
            ) from e

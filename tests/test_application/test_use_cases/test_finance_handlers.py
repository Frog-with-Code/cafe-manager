import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from cafe_manager.application.use_cases.finance_handlers import (
    FinanceInvestHandler,
    FinanceStatsHandler,
    FinanceHistoryHandler,
    FinanceSetPrimaryHandler,
)
from cafe_manager.common.exceptions import AccountNotFoundError
from cafe_manager.domain.entities.finance import Money, Account, Transaction, TransactionType
from cafe_manager.application.interfaces import FinanceRepo


class TestFinanceInvestHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=FinanceRepo)

    @pytest.fixture
    def mock_uow(self, mock_repo):
        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.finance_repo = mock_repo
        return uow

    def test_handle_success_primary(self, mock_repo, mock_uow):
        account = Account(balance=Money(Decimal("100.00")))
        mock_repo.get_primary.return_value = account
        
        handler = FinanceInvestHandler(mock_uow)
        amount = Money(Decimal("50.00"))
        handler.handle(amount, None, "Test Investment")
        
        assert account.balance == Money(Decimal("150.00"))
        mock_repo.save.assert_called_once_with(account)

    def test_handle_success_by_id(self, mock_repo, mock_uow):
        acc_id = uuid4()
        account = Account(account_id=acc_id, balance=Money(Decimal("0.00")))
        mock_repo.get_by_id.return_value = account
        
        handler = FinanceInvestHandler(mock_uow)
        handler.handle(Money(Decimal("10.00")), acc_id, "ID Investment")
        
        assert account.balance == Money(Decimal("10.00"))
        mock_repo.get_by_id.assert_called_once_with(acc_id)

    def test_handle_account_not_found(self, mock_repo, mock_uow):
        mock_repo.get_primary.return_value = None
        handler = FinanceInvestHandler(mock_uow)
        
        with pytest.raises(AccountNotFoundError):
            handler.handle(Money(Decimal("10")), None, "Msg")


class TestFinanceStatsHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=FinanceRepo)

    @pytest.fixture
    def mock_uow(self, mock_repo):
        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.finance_repo = mock_repo
        return uow

    def test_handle_profit_stats(self, mock_repo, mock_uow):
        acc_id = uuid4()
        account = Account(account_id=acc_id, balance=Money(Decimal("500.00")))
        mock_repo.get_primary.return_value = account
        
        transactions = [
            Transaction(TransactionType.INCOME, Money(Decimal("200.00"))),
            Transaction(TransactionType.EXPENSE, Money(Decimal("50.00"))),
        ]
        mock_repo.get_transactions_by_period.return_value = transactions
        
        handler = FinanceStatsHandler(mock_uow)
        result = handler.handle(None, None, None)
        
        assert result["id"] == acc_id
        assert result["income"] == Money(Decimal("200.00"))
        assert result["expense"] == Money(Decimal("50.00"))
        assert result["profit_abs"] == Money(Decimal("150.00"))
        assert result["is_loss"] is False

    def test_handle_loss_stats(self, mock_repo, mock_uow):
        account = Account(balance=Money(Decimal("10.00")))
        mock_repo.get_primary.return_value = account
        
        transactions = [
            Transaction(TransactionType.INCOME, Money(Decimal("10.00"))),
            Transaction(TransactionType.EXPENSE, Money(Decimal("100.00"))),
        ]
        mock_repo.get_transactions_by_period.return_value = transactions
        
        handler = FinanceStatsHandler(mock_uow)
        result = handler.handle(None, None, None)
        
        assert result["profit_abs"] == Money(Decimal("90.00"))
        assert result["is_loss"] is True

    def test_handle_account_not_found(self, mock_repo, mock_uow):
        mock_repo.get_by_id.return_value = None
        handler = FinanceStatsHandler(mock_uow)
        with pytest.raises(AccountNotFoundError):
            handler.handle(uuid4(), None, None)


class TestFinanceHistoryHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=FinanceRepo)

    @pytest.fixture
    def mock_uow(self, mock_repo):
        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.finance_repo = mock_repo
        return uow

    def test_handle_success(self, mock_repo, mock_uow):
        acc_id = uuid4()
        account = Account(account_id=acc_id)
        mock_repo.get_primary.return_value = account
        
        history = [MagicMock(spec=Transaction) for _ in range(3)]
        mock_repo.get_latest_transactions.return_value = history
        
        handler = FinanceHistoryHandler(mock_uow)
        result = handler.handle(None, 5)
        
        assert result == history
        mock_repo.get_latest_transactions.assert_called_once_with(acc_id, 5)

    def test_handle_empty_history(self, mock_repo, mock_uow):
        mock_repo.get_primary.return_value = Account()
        mock_repo.get_latest_transactions.return_value = None
        
        handler = FinanceHistoryHandler(mock_uow)
        assert handler.handle(None, 5) == []

    def test_handle_account_not_found(self, mock_repo, mock_uow):
        mock_repo.get_by_id.return_value = None
        handler = FinanceHistoryHandler(mock_uow)
        with pytest.raises(AccountNotFoundError):
            handler.handle(uuid4(), 5)


class TestFinanceSetPrimaryHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=FinanceRepo)

    @pytest.fixture
    def mock_uow(self, mock_repo):
        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.finance_repo = mock_repo
        return uow

    def test_handle_success(self, mock_repo, mock_uow):
        acc_id = uuid4()
        handler = FinanceSetPrimaryHandler(mock_uow)
        handler.handle(acc_id)
        mock_repo.set_primary.assert_called_once_with(acc_id)

    def test_handle_account_not_found(self, mock_repo, mock_uow):
        acc_id = uuid4()
        mock_repo.set_primary.side_effect = AccountNotFoundError("Error")
        
        handler = FinanceSetPrimaryHandler(mock_uow)
        with pytest.raises(AccountNotFoundError):
            handler.handle(acc_id)
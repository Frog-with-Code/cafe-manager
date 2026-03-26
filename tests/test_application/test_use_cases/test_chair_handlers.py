import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from decimal import Decimal

from cafe_manager.application.use_cases.chair_handlers import (
    ChairBuyHandler,
    ChairDiscardHandler,
    ChairInfoHandler,
)
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ChairNotFoundError,
    InsufficientBudgetError,
)
from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.domain.entities.equipment import Chair, Table


class TestChairBuyHandler:
    @pytest.fixture
    def mock_repos(self):
        return MagicMock(), MagicMock()

    def test_handle_success(self, mock_repos):
        finance_repo, chair_repo = mock_repos
        account = Account(balance=Money(Decimal("100.00")))
        finance_repo.get_primary.return_value = account
        
        handler = ChairBuyHandler(finance_repo, chair_repo)
        price = Money(Decimal("50.00"))
        handler.handle(price=price, account_id=None)
        
        assert account.balance == Money(Decimal("50.00"))
        finance_repo.save.assert_called_once_with(account)
        chair_repo.save.assert_called_once()
        assert isinstance(chair_repo.save.call_args[0][0], Chair)

    def test_handle_account_not_found(self, mock_repos):
        finance_repo, chair_repo = mock_repos
        finance_repo.get_by_id.return_value = None
        
        handler = ChairBuyHandler(finance_repo, chair_repo)
        with pytest.raises(AccountNotFoundError):
            handler.handle(Money(Decimal("10")), uuid4())

    def test_handle_insufficient_budget(self, mock_repos):
        finance_repo, chair_repo = mock_repos
        account = Account(balance=Money(Decimal("5.00")))
        finance_repo.get_primary.return_value = account
        
        handler = ChairBuyHandler(finance_repo, chair_repo)
        with pytest.raises(InsufficientBudgetError):
            handler.handle(Money(Decimal("10.00")), None)


class TestChairDiscardHandler:
    @pytest.fixture
    def mock_repos(self):
        return MagicMock(), MagicMock()

    def test_handle_success_with_table(self, mock_repos):
        chair_repo, table_repo = mock_repos
        chair = Chair(chair_id=1, table_id=10)
        table = MagicMock(spec=Table)
        
        chair_repo.get_by_id.return_value = chair
        table_repo.get_by_id.return_value = table
        
        handler = ChairDiscardHandler(chair_repo, table_repo)
        handler.handle(chair_id=1)
        
        table.remove_chair.assert_called_once_with(1)
        table_repo.save.assert_called_once_with(table)
        chair_repo.delete_by_id.assert_called_once_with(1)

    def test_handle_success_no_table(self, mock_repos):
        chair_repo, table_repo = mock_repos
        chair = Chair(chair_id=1, table_id=None)
        chair_repo.get_by_id.return_value = chair
        
        handler = ChairDiscardHandler(chair_repo, table_repo)
        handler.handle(1)
        
        table_repo.save.assert_not_called()
        chair_repo.delete_by_id.assert_called_once_with(1)

    def test_handle_chair_not_found(self, mock_repos):
        chair_repo, table_repo = mock_repos
        chair_repo.get_by_id.return_value = None
        
        handler = ChairDiscardHandler(chair_repo, table_repo)
        with pytest.raises(ChairNotFoundError):
            handler.handle(99)


class TestChairInfoHandler:
    def test_handle_returns_list(self):
        mock_repo = MagicMock()
        chairs = [Chair(chair_id=1), Chair(chair_id=2)]
        mock_repo.get_all.return_value = chairs
        
        handler = ChairInfoHandler(mock_repo)
        result = handler.handle()
        
        assert result == chairs

    def test_handle_returns_empty_list_on_none(self):
        mock_repo = MagicMock()
        mock_repo.get_all.return_value = None
        
        handler = ChairInfoHandler(mock_repo)
        result = handler.handle()
        
        assert result == []
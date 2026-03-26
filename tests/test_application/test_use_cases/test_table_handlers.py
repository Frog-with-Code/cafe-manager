import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from decimal import Decimal

from cafe_manager.application.use_cases.table_handlers import (
    TableBuyHandler,
    TableDiscardHandler,
    TableInfoHandler,
    TableReserveHandler,
    AssignChairToTableHandler,
    TableFreeHandler,
)
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ChairNotFoundError,
    InsufficientBudgetError,
    TableBusyError,
    TableNotFoundError,
    TablePlacesError,
)
from cafe_manager.domain.entities.equipment import Table, Chair
from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.domain.services.seating_service import SeatingService
from cafe_manager.application.interfaces import (
    ChairRepo,
    FinanceRepo,
    OrderRepo,
    TableRepo,
)


class TestTableBuyHandler:
    @pytest.fixture
    def mock_deps(self):
        return MagicMock(spec=FinanceRepo), MagicMock(spec=TableRepo)

    def test_handle_success(self, mock_deps):
        fin_repo, table_repo = mock_deps
        account = Account(balance=Money(Decimal("1000.00")))
        fin_repo.get_primary.return_value = account
        
        handler = TableBuyHandler(fin_repo, table_repo)
        price = Money(Decimal("200.00"))
        handler.handle(price, 4, None)
        
        assert account.balance == Money(Decimal("800.00"))
        fin_repo.save.assert_called_once_with(account)
        table_repo.save.assert_called_once()
        saved_table = table_repo.save.call_args[0][0]
        assert isinstance(saved_table, Table)
        assert saved_table.max_places == 4

    def test_handle_account_not_found(self, mock_deps):
        fin_repo, table_repo = mock_deps
        fin_repo.get_by_id.return_value = None
        
        handler = TableBuyHandler(fin_repo, table_repo)
        with pytest.raises(AccountNotFoundError):
            handler.handle(Money.from_any(10), 2, uuid4())

    def test_handle_insufficient_budget(self, mock_deps):
        fin_repo, table_repo = mock_deps
        account = Account(balance=Money(Decimal("10.00")))
        fin_repo.get_primary.return_value = account
        
        handler = TableBuyHandler(fin_repo, table_repo)
        with pytest.raises(InsufficientBudgetError):
            handler.handle(Money(Decimal("50.00")), 4, None)


class TestTableDiscardHandler:
    @pytest.fixture
    def mock_deps(self):
        return MagicMock(spec=TableRepo), MagicMock(spec=ChairRepo)

    def test_handle_success(self, mock_deps):
        table_repo, chair_repo = mock_deps
        table_repo.get_by_id.return_value = MagicMock(spec=Table)
        
        handler = TableDiscardHandler(table_repo, chair_repo)
        handler.handle(1)
        
        table_repo.delete_by_id.assert_called_once_with(1)
        chair_repo.delete_table_by_id.assert_called_once_with(1)

    def test_handle_not_found(self, mock_deps):
        table_repo, chair_repo = mock_deps
        table_repo.get_by_id.return_value = None
        
        handler = TableDiscardHandler(table_repo, chair_repo)
        with pytest.raises(TableNotFoundError):
            handler.handle(99)


class TestTableInfoHandler:
    def test_handle_returns_tables(self):
        repo = MagicMock(spec=TableRepo)
        tables = [MagicMock(spec=Table), MagicMock(spec=Table)]
        repo.get_all.return_value = tables
        
        handler = TableInfoHandler(repo)
        assert handler.handle() == tables

    def test_handle_returns_empty_list_on_none(self):
        repo = MagicMock(spec=TableRepo)
        repo.get_all.return_value = None
        
        handler = TableInfoHandler(repo)
        assert handler.handle() == []


class TestTableReserveHandler:
    @pytest.fixture
    def mock_deps(self):
        return MagicMock(spec=TableRepo), MagicMock(spec=ChairRepo), MagicMock(spec=SeatingService)

    def test_handle_success(self, mock_deps):
        table_repo, chair_repo, service = mock_deps
        table = MagicMock(spec=Table)
        table.table_id = 5
        
        table_repo.get_all.return_value = [table]
        chair_repo.get_free.return_value = [MagicMock(spec=Chair)]
        service.reserve.return_value = (table, [table], [MagicMock(spec=Chair)])
        
        handler = TableReserveHandler(table_repo, chair_repo, service)
        result = handler.handle(2)
        
        assert result == 5
        table_repo.save_many.assert_called_once()
        chair_repo.save_many.assert_called_once()

    def test_handle_no_tables(self, mock_deps):
        table_repo, chair_repo, service = mock_deps
        table_repo.get_all.return_value = None
        
        handler = TableReserveHandler(table_repo, chair_repo, service)
        with pytest.raises(TableNotFoundError):
            handler.handle(2)

    def test_handle_no_chairs(self, mock_deps):
        table_repo, chair_repo, service = mock_deps
        table_repo.get_all.return_value = [MagicMock(spec=Table)]
        chair_repo.get_free.return_value = None
        
        handler = TableReserveHandler(table_repo, chair_repo, service)
        with pytest.raises(ChairNotFoundError):
            handler.handle(2)


class TestAssignChairToTableHandler:
    @pytest.fixture
    def mock_deps(self):
        return MagicMock(spec=TableRepo), MagicMock(spec=ChairRepo)

    def test_handle_success_new_assignment(self, mock_deps):
        table_repo, chair_repo = mock_deps
        target_table = MagicMock(spec=Table)
        target_table.table_id = 1
        chair = MagicMock(spec=Chair)
        chair._table_id = None
        
        table_repo.get_by_id.return_value = target_table
        chair_repo.get_by_id.return_value = chair
        
        handler = AssignChairToTableHandler(table_repo, chair_repo)
        handler.handle(1, 10)
        
        target_table.add_chair.assert_called_once_with(10)
        chair.assign_to_table.assert_called_once_with(1)
        table_repo.save.assert_called_once_with(target_table)
        chair_repo.save.assert_called_once_with(chair)

    def test_handle_success_reassignment(self, mock_deps):
        table_repo, chair_repo = mock_deps
        target_table = MagicMock(spec=Table)
        target_table.table_id = 2
        prev_table = MagicMock(spec=Table)
        chair = MagicMock(spec=Chair)
        chair._table_id = 1
        
        table_repo.get_by_id.side_effect = [target_table, prev_table]
        chair_repo.get_by_id.return_value = chair
        
        handler = AssignChairToTableHandler(table_repo, chair_repo)
        handler.handle(2, 10)
        
        prev_table.remove_chair.assert_called_once_with(10)
        target_table.add_chair.assert_called_once_with(10)
        assert table_repo.save.call_count == 2

    def test_handle_table_not_found(self, mock_deps):
        table_repo, chair_repo = mock_deps
        table_repo.get_by_id.return_value = None
        
        handler = AssignChairToTableHandler(table_repo, chair_repo)
        with pytest.raises(TableNotFoundError):
            handler.handle(1, 10)


class TestTableFreeHandler:
    @pytest.fixture
    def mock_deps(self):
        return MagicMock(spec=TableRepo), MagicMock(spec=ChairRepo), MagicMock(spec=OrderRepo)

    def test_handle_success(self, mock_deps):
        table_repo, chair_repo, order_repo = mock_deps
        table = MagicMock(spec=Table)
        chair = MagicMock(spec=Chair)
        
        table_repo.get_by_id.return_value = table
        order_repo.get_active_by_table_id.return_value = None
        chair_repo.get_busy_by_table_id.return_value = [chair]
        
        handler = TableFreeHandler(table_repo, chair_repo, order_repo)
        handler.handle(1)
        
        table.free.assert_called_once()
        chair.free.assert_called_once()

    def test_handle_busy_with_orders(self, mock_deps):
        table_repo, chair_repo, order_repo = mock_deps
        table_repo.get_by_id.return_value = MagicMock(spec=Table)
        order_repo.get_active_by_table_id.return_value = [MagicMock()]
        
        handler = TableFreeHandler(table_repo, chair_repo, order_repo)
        with pytest.raises(TableBusyError):
            handler.handle(1)
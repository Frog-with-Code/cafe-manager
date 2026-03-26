import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from decimal import Decimal

from cafe_manager.application.use_cases.machine_handlers import (
    CoffeeMachineBuyHandler,
    CoffeeMachineDiscardHandler,
    CoffeeMachineInfoHandler,
    CoffeeMachineServiceHandler,
    CoffeeMachineResumeHandler,
)
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CoffeeMachineNotFoundError,
    InsufficientBudgetError,
)
from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.domain.entities.equipment import CoffeeMachine
from cafe_manager.application.interfaces import CoffeeMachineRepo, FinanceRepo


class TestCoffeeMachineBuyHandler:
    @pytest.fixture
    def mock_deps(self):
        return MagicMock(spec=FinanceRepo), MagicMock(spec=CoffeeMachineRepo)

    def test_handle_success(self, mock_deps):
        fin_repo, machine_repo = mock_deps
        account = Account(balance=Money(Decimal("5000.00")))
        fin_repo.get_primary.return_value = account
        
        handler = CoffeeMachineBuyHandler(fin_repo, machine_repo)
        price = Money(Decimal("2000.00"))
        
        handler.handle(price, "SuperCoffee 3000", 500, None)
        
        assert account.balance == Money(Decimal("3000.00"))
        fin_repo.save.assert_called_once_with(account)
        machine_repo.save.assert_called_once()
        saved_machine = machine_repo.save.call_args[0][0]
        assert isinstance(saved_machine, CoffeeMachine)
        assert saved_machine.model == "SuperCoffee 3000"

    def test_handle_account_not_found(self, mock_deps):
        fin_repo, machine_repo = mock_deps
        fin_repo.get_by_id.return_value = None
        
        handler = CoffeeMachineBuyHandler(fin_repo, machine_repo)
        with pytest.raises(AccountNotFoundError):
            handler.handle(Money.from_any(10), "Model", 100, uuid4())

    def test_handle_insufficient_budget(self, mock_deps):
        fin_repo, machine_repo = mock_deps
        account = Account(balance=Money(Decimal("100.00")))
        fin_repo.get_primary.return_value = account
        
        handler = CoffeeMachineBuyHandler(fin_repo, machine_repo)
        with pytest.raises(InsufficientBudgetError):
            handler.handle(Money(Decimal("200.00")), "Model", 100, None)


class TestCoffeeMachineDiscardHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=CoffeeMachineRepo)

    def test_handle_success(self, mock_repo):
        mock_repo.get_by_id.return_value = MagicMock(spec=CoffeeMachine)
        
        handler = CoffeeMachineDiscardHandler(mock_repo)
        handler.handle(1)
        
        mock_repo.delete_by_id.assert_called_once_with(1)

    def test_handle_not_found(self, mock_repo):
        mock_repo.get_by_id.return_value = None
        
        handler = CoffeeMachineDiscardHandler(mock_repo)
        with pytest.raises(CoffeeMachineNotFoundError):
            handler.handle(999)


class TestCoffeeMachineInfoHandler:
    def test_handle_returns_machines(self):
        repo = MagicMock(spec=CoffeeMachineRepo)
        machines = [MagicMock(spec=CoffeeMachine), MagicMock(spec=CoffeeMachine)]
        repo.get_all.return_value = machines
        
        handler = CoffeeMachineInfoHandler(repo)
        result = handler.handle()
        
        assert result == machines

    def test_handle_returns_empty_list_on_none(self):
        repo = MagicMock(spec=CoffeeMachineRepo)
        repo.get_all.return_value = None
        
        handler = CoffeeMachineInfoHandler(repo)
        assert handler.handle() == []


class TestCoffeeMachineServiceHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=CoffeeMachineRepo)

    def test_handle_success(self, mock_repo):
        machine = MagicMock(spec=CoffeeMachine)
        mock_repo.get_by_id.return_value = machine
        
        handler = CoffeeMachineServiceHandler(mock_repo)
        handler.handle(123)
        
        mock_repo.get_by_id.assert_called_once_with(123)
        machine.service.assert_called_once()

    def test_handle_not_found(self, mock_repo):
        mock_repo.get_by_id.return_value = None
        handler = CoffeeMachineServiceHandler(mock_repo)
        
        with pytest.raises(CoffeeMachineNotFoundError):
            handler.handle(1)


class TestCoffeeMachineResumeHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=CoffeeMachineRepo)

    def test_handle_success(self, mock_repo):
        machine = MagicMock(spec=CoffeeMachine)
        mock_repo.get_by_id.return_value = machine
        
        handler = CoffeeMachineResumeHandler(mock_repo)
        handler.handle(456)
        
        mock_repo.get_by_id.assert_called_once_with(456)
        machine.resume.assert_called_once()

    def test_handle_not_found(self, mock_repo):
        mock_repo.get_by_id.return_value = None
        handler = CoffeeMachineResumeHandler(mock_repo)
        
        with pytest.raises(CoffeeMachineNotFoundError):
            handler.handle(1)
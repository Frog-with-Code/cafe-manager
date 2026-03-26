import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from decimal import Decimal

from cafe_manager.application.use_cases.order_handlers import (
    OrderCreateHandler,
    OrderPayHandler,
    OrderServeHandler,
    OrderInfoHandler,
)
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    ClientNotFoundError,
    CoffeeMachineNotFoundError,
    EmployeeNotAssignedError,
    EmployeeNotFoundError,
    InsufficientStocksError,
    MenuItemNotFoundError,
    MenuItemRepeatError,
    OrderNotFoundError,
    TableNotFoundError,
)
from cafe_manager.domain.entities.equipment import CoffeeMachine, Table, Chair, TableState
from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.domain.entities.menu import MenuItem, Ingredient
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.entities.people import Client, Employee
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.domain.services.ingredient_calculator import IngredientCalculator
from cafe_manager.domain.services.payment_service import PaymentService
from cafe_manager.application.interfaces import (
    ChairRepo,
    ClientRepo,
    CoffeeMachineRepo,
    EmployeeRepo,
    FinanceRepo,
    InventoryRepo,
    MenuRepo,
    OrderRepo,
    TableRepo,
)


class TestOrderCreateHandler:
    @pytest.fixture
    def mock_deps(self):
        id_gen = MagicMock(spec=IDGeneratingService)
        id_gen.max_attempts = 100
        return {
            "order_repo": MagicMock(spec=OrderRepo),
            "inventory_repo": MagicMock(spec=InventoryRepo),
            "menu_repo": MagicMock(spec=MenuRepo),
            "table_repo": MagicMock(spec=TableRepo),
            "chair_repo": MagicMock(spec=ChairRepo),
            "ingredient_calculator": MagicMock(spec=IngredientCalculator),
            "id_generator": id_gen,
        }

    def test_handle_success_with_table(self, mock_deps):
        item = MagicMock(spec=MenuItem)
        item.price = Money(Decimal("10.00"))
        
        mock_deps["menu_repo"].get_by_name.return_value = item
        mock_deps["ingredient_calculator"].calculate.return_value = {}
        mock_deps["order_repo"].get_by_id.return_value = None
        mock_deps["id_generator"].generate_unique_code.return_value = "ord-SUCCESS"
        
        table = MagicMock(spec=Table)
        table._state = TableState.AVAILABLE
        mock_deps["table_repo"].get_by_id.return_value = table
        mock_deps["chair_repo"].get_busy_by_table_id.return_value = []
        
        handler = OrderCreateHandler(**mock_deps)
        order_id = handler.handle([("Coffee", 1)], table_id=1, continue_session=False)
        
        assert order_id == "ord-SUCCESS"
        table.occupy.assert_called_once()
        mock_deps["order_repo"].save.assert_called_once()

    def test_handle_menu_item_not_found(self, mock_deps):
        mock_deps["menu_repo"].get_by_name.return_value = None
        handler = OrderCreateHandler(**mock_deps)
        
        with pytest.raises(MenuItemNotFoundError):
            handler.handle([("GhostItem", 1)], None, False)

    def test_handle_menu_item_repeat(self, mock_deps):
        item = MagicMock(spec=MenuItem)
        item.price = Money(Decimal("5.00"))
        mock_deps["menu_repo"].get_by_name.return_value = item
        
        handler = OrderCreateHandler(**mock_deps)
        with pytest.raises(MenuItemRepeatError):
            handler.handle([("Coffee", 1), ("Coffee", 2)], None, False)

    def test_handle_insufficient_stocks(self, mock_deps):
        item = MagicMock(spec=MenuItem)
        item.price = Money(Decimal("5.00"))
        mock_deps["menu_repo"].get_by_name.return_value = item
        
        ing = MagicMock(spec=Ingredient)
        ing.name = "Milk"
        mock_deps["ingredient_calculator"].calculate.return_value = {ing: 100.0}
        mock_deps["inventory_repo"].get_free_by_name.return_value = 10.0
        mock_deps["order_repo"].get_by_id.return_value = None
        
        handler = OrderCreateHandler(**mock_deps)
        with pytest.raises(InsufficientStocksError):
            handler.handle([("Latte", 1)], None, False)

    def test_handle_table_not_found(self, mock_deps):
        item = MagicMock(spec=MenuItem)
        item.price = Money(Decimal("5.00"))
        mock_deps["menu_repo"].get_by_name.return_value = item
        mock_deps["table_repo"].get_by_id.return_value = None
        
        handler = OrderCreateHandler(**mock_deps)
        with pytest.raises(TableNotFoundError):
            handler.handle([("Tea", 1)], table_id=99, continue_session=False)


class TestOrderPayHandler:
    @pytest.fixture
    def mock_deps(self):
        return {
            "order_repo": MagicMock(spec=OrderRepo),
            "finance_repo": MagicMock(spec=FinanceRepo),
            "client_repo": MagicMock(spec=ClientRepo),
            "payment_service": MagicMock(spec=PaymentService),
        }

    def test_handle_success(self, mock_deps):
        order = MagicMock(spec=Order)
        account = MagicMock(spec=Account)
        client = MagicMock(spec=Client)
        
        mock_deps["order_repo"].get_by_id.return_value = order
        mock_deps["finance_repo"].get_primary.return_value = account
        mock_deps["client_repo"].get_by_id.return_value = client
        mock_deps["payment_service"].process.return_value = (order, account, client)
        
        handler = OrderPayHandler(**mock_deps)
        handler.handle("ord-1", Money(Decimal("50.00")), None, "cli-1")
        
        mock_deps["payment_service"].process.assert_called_once()
        mock_deps["order_repo"].save.assert_called_once_with(order)
        mock_deps["finance_repo"].save.assert_called_once_with(account)
        mock_deps["client_repo"].save.assert_called_once_with(client)

    def test_handle_order_not_found(self, mock_deps):
        mock_deps["order_repo"].get_by_id.return_value = None
        handler = OrderPayHandler(**mock_deps)
        
        with pytest.raises(OrderNotFoundError):
            handler.handle("ghost", Money(Decimal("10")), None, None)

    def test_handle_account_not_found(self, mock_deps):
        mock_deps["order_repo"].get_by_id.return_value = MagicMock(spec=Order)
        mock_deps["finance_repo"].get_by_id.return_value = None
        
        handler = OrderPayHandler(**mock_deps)
        with pytest.raises(AccountNotFoundError):
            handler.handle("ord-1", Money(Decimal("10")), uuid4(), None)

    def test_handle_client_not_found(self, mock_deps):
        mock_deps["order_repo"].get_by_id.return_value = MagicMock(spec=Order)
        mock_deps["finance_repo"].get_primary.return_value = MagicMock(spec=Account)
        mock_deps["client_repo"].get_by_id.return_value = None
        
        handler = OrderPayHandler(**mock_deps)
        with pytest.raises(ClientNotFoundError):
            handler.handle("ord-1", Money(Decimal("10")), None, "ghost-client")


class TestOrderServeHandler:
    @pytest.fixture
    def mock_deps(self):
        return {
            "order_repo": MagicMock(spec=OrderRepo),
            "employee_repo": MagicMock(spec=EmployeeRepo),
            "machine_repo": MagicMock(spec=CoffeeMachineRepo),
        }

    def test_handle_order_not_found(self, mock_deps):
        mock_deps["order_repo"].get_by_id.return_value = None
        handler = OrderServeHandler(**mock_deps)
        
        with pytest.raises(OrderNotFoundError):
            handler.handle("ord-ghost")

    def test_handle_employee_not_assigned(self, mock_deps):
        order = MagicMock(spec=Order)
        order.employee_id = None
        mock_deps["order_repo"].get_by_id.return_value = order
        
        handler = OrderServeHandler(**mock_deps)
        with pytest.raises(EmployeeNotAssignedError):
            handler.handle("ord-1")

    def test_handle_employee_not_found(self, mock_deps):
        order = MagicMock(spec=Order)
        order.employee_id = "emp-missing"
        mock_deps["order_repo"].get_by_id.return_value = order
        mock_deps["employee_repo"].get_by_id.return_value = None
        
        handler = OrderServeHandler(**mock_deps)
        with pytest.raises(EmployeeNotFoundError):
            handler.handle("ord-1")

    def test_handle_coffee_machine_not_found(self, mock_deps):
        order = MagicMock(spec=Order)
        order.employee_id = "emp-1"
        order.machine_id = 99
        employee = MagicMock(spec=Employee)
        
        mock_deps["order_repo"].get_by_id.return_value = order
        mock_deps["employee_repo"].get_by_id.return_value = employee
        mock_deps["machine_repo"].get_by_id.return_value = None
        
        handler = OrderServeHandler(**mock_deps)
        with pytest.raises(CoffeeMachineNotFoundError):
            handler.handle("ord-1")

    def test_handle_success_without_machine(self, mock_deps):
        order = MagicMock(spec=Order)
        order.employee_id = "emp-1"
        order.machine_id = None
        employee = MagicMock(spec=Employee)
        
        mock_deps["order_repo"].get_by_id.return_value = order
        mock_deps["employee_repo"].get_by_id.return_value = employee
        
        handler = OrderServeHandler(**mock_deps)
        handler.handle("ord-1")
        
        order.complete.assert_called_once()
        employee.rest.assert_called_once()
        mock_deps["order_repo"].save.assert_called_once_with(order)
        mock_deps["employee_repo"].save.assert_called_once_with(employee)
        mock_deps["machine_repo"].save.assert_not_called()

    def test_handle_success_with_machine(self, mock_deps):
        order = MagicMock(spec=Order)
        order.employee_id = "emp-1"
        order.machine_id = 10
        employee = MagicMock(spec=Employee)
        machine = MagicMock(spec=CoffeeMachine)
        
        mock_deps["order_repo"].get_by_id.return_value = order
        mock_deps["employee_repo"].get_by_id.return_value = employee
        mock_deps["machine_repo"].get_by_id.return_value = machine
        
        handler = OrderServeHandler(**mock_deps)
        handler.handle("ord-1")
        
        machine.stop.assert_called_once()
        order.complete.assert_called_once()
        employee.rest.assert_called_once()
        
        mock_deps["order_repo"].save.assert_called_once_with(order)
        mock_deps["employee_repo"].save.assert_called_once_with(employee)
        mock_deps["machine_repo"].save.assert_called_once_with(machine)


class TestOrderInfoHandler:
    def test_handle_returns_orders(self):
        repo = MagicMock(spec=OrderRepo)
        orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
        repo.get_all_active.return_value = orders
        
        handler = OrderInfoHandler(repo)
        result = handler.handle()
        
        assert result == orders

    def test_handle_returns_empty_list(self):
        repo = MagicMock(spec=OrderRepo)
        repo.get_all_active.return_value = None
        
        handler = OrderInfoHandler(repo)
        assert handler.handle() == []
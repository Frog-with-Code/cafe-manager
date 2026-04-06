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
        order_repo = MagicMock(spec=OrderRepo)
        inventory_repo = MagicMock(spec=InventoryRepo)
        menu_repo = MagicMock(spec=MenuRepo)
        table_repo = MagicMock(spec=TableRepo)
        chair_repo = MagicMock(spec=ChairRepo)

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = order_repo
        uow.inventory_repo = inventory_repo
        uow.menu_repo = menu_repo
        uow.table_repo = table_repo
        uow.chair_repo = chair_repo

        return {
            "uow": uow,
            "order_repo": order_repo,
            "inventory_repo": inventory_repo,
            "menu_repo": menu_repo,
            "table_repo": table_repo,
            "chair_repo": chair_repo,
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
        
        handler = OrderCreateHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
            id_generator=mock_deps["id_generator"],
        )
        order_id = handler.handle([("Coffee", 1)], table_id=1, continue_session=False)
        
        assert order_id == "ord-SUCCESS"
        table.occupy.assert_called_once()
        mock_deps["order_repo"].save.assert_called_once()

    def test_handle_menu_item_not_found(self, mock_deps):
        mock_deps["menu_repo"].get_by_name.return_value = None
        handler = OrderCreateHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
            id_generator=mock_deps["id_generator"],
        )
        
        with pytest.raises(MenuItemNotFoundError):
            handler.handle([("GhostItem", 1)], None, False)

    def test_handle_menu_item_repeat(self, mock_deps):
        item = MagicMock(spec=MenuItem)
        item.price = Money(Decimal("5.00"))
        mock_deps["menu_repo"].get_by_name.return_value = item
        
        handler = OrderCreateHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
            id_generator=mock_deps["id_generator"],
        )
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
        
        handler = OrderCreateHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
            id_generator=mock_deps["id_generator"],
        )
        with pytest.raises(InsufficientStocksError):
            handler.handle([("Latte", 1)], None, False)

    def test_handle_table_not_found(self, mock_deps):
        item = MagicMock(spec=MenuItem)
        item.price = Money(Decimal("5.00"))
        mock_deps["menu_repo"].get_by_name.return_value = item
        mock_deps["table_repo"].get_by_id.return_value = None
        
        handler = OrderCreateHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
            id_generator=mock_deps["id_generator"],
        )
        with pytest.raises(TableNotFoundError):
            handler.handle([("Tea", 1)], table_id=99, continue_session=False)


class TestOrderPayHandler:
    @pytest.fixture
    def mock_deps(self):
        order_repo = MagicMock(spec=OrderRepo)
        finance_repo = MagicMock(spec=FinanceRepo)
        client_repo = MagicMock(spec=ClientRepo)

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = order_repo
        uow.finance_repo = finance_repo
        uow.client_repo = client_repo

        return {
            "uow": uow,
            "order_repo": order_repo,
            "finance_repo": finance_repo,
            "client_repo": client_repo,
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
        
        handler = OrderPayHandler(
            uow=mock_deps["uow"], payment_service=mock_deps["payment_service"]
        )
        handler.handle("ord-1", Money(Decimal("50.00")), None, "cli-1")
        
        mock_deps["payment_service"].process.assert_called_once()
        mock_deps["order_repo"].save.assert_called_once_with(order)
        mock_deps["finance_repo"].save.assert_called_once_with(account)
        mock_deps["client_repo"].save.assert_called_once_with(client)

    def test_handle_order_not_found(self, mock_deps):
        mock_deps["order_repo"].get_by_id.return_value = None
        handler = OrderPayHandler(
            uow=mock_deps["uow"], payment_service=mock_deps["payment_service"]
        )
        
        with pytest.raises(OrderNotFoundError):
            handler.handle("ghost", Money(Decimal("10")), None, None)

    def test_handle_account_not_found(self, mock_deps):
        mock_deps["order_repo"].get_by_id.return_value = MagicMock(spec=Order)
        mock_deps["finance_repo"].get_by_id.return_value = None
        
        handler = OrderPayHandler(
            uow=mock_deps["uow"], payment_service=mock_deps["payment_service"]
        )
        with pytest.raises(AccountNotFoundError):
            handler.handle("ord-1", Money(Decimal("10")), uuid4(), None)

    def test_handle_client_not_found(self, mock_deps):
        mock_deps["order_repo"].get_by_id.return_value = MagicMock(spec=Order)
        mock_deps["finance_repo"].get_primary.return_value = MagicMock(spec=Account)
        mock_deps["client_repo"].get_by_id.return_value = None
        
        handler = OrderPayHandler(
            uow=mock_deps["uow"], payment_service=mock_deps["payment_service"]
        )
        with pytest.raises(ClientNotFoundError):
            handler.handle("ord-1", Money(Decimal("10")), None, "ghost-client")


class TestOrderServeHandler:
    @pytest.fixture
    def mock_repos(self, mocker):
        order_repo = mocker.MagicMock()
        employee_repo = mocker.MagicMock()

        uow = mocker.MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = order_repo
        uow.employee_repo = employee_repo

        return {
            "uow": uow,
            "order_repo": order_repo,
            "employee_repo": employee_repo,
        }

    def test_handle_success(self, mocker, mock_repos):
        order_repo = mock_repos["order_repo"]
        employee_repo = mock_repos["employee_repo"]
        handler = OrderServeHandler(mock_repos["uow"])

        mock_order = mocker.MagicMock()
        mock_order.employee_id = "emp-777"
        order_repo.get_by_id.return_value = mock_order

        mock_employee = mocker.MagicMock()
        employee_repo.get_by_id.return_value = mock_employee

        handler.handle("ord-123")

        mock_order.complete.assert_called_once()
        mock_employee.rest.assert_called_once()

        order_repo.save.assert_called_once_with(mock_order)
        employee_repo.save.assert_called_once_with(mock_employee)

    def test_handle_order_not_found(self, mock_repos):
        order_repo = mock_repos["order_repo"]
        handler = OrderServeHandler(mock_repos["uow"])

        order_repo.get_by_id.return_value = None

        with pytest.raises(OrderNotFoundError) as exc:
            handler.handle("non-existent")
        
        assert "Order with ID non-existent was not found" in str(exc.value)

    def test_handle_employee_not_assigned(self, mocker, mock_repos):
        order_repo = mock_repos["order_repo"]
        handler = OrderServeHandler(mock_repos["uow"])

        mock_order = mocker.MagicMock()
        mock_order.employee_id = None 
        order_repo.get_by_id.return_value = mock_order

        with pytest.raises(EmployeeNotAssignedError) as exc:
            handler.handle("ord-123")
        
        assert "Employee not assigned to the order" in str(exc.value)
        mock_order.complete.assert_called_once()

    def test_handle_employee_not_found_in_repo(self, mocker, mock_repos):
        order_repo = mock_repos["order_repo"]
        employee_repo = mock_repos["employee_repo"]
        handler = OrderServeHandler(mock_repos["uow"])

        mock_order = mocker.MagicMock()
        mock_order.employee_id = "ghost-id"
        order_repo.get_by_id.return_value = mock_order
        
        employee_repo.get_by_id.return_value = None

        with pytest.raises(EmployeeNotFoundError) as exc:
            handler.handle("ord-123")
        
        assert "Employee with ID ghost-id was not found" in str(exc.value)


class TestOrderInfoHandler:
    def test_handle_returns_orders(self):
        repo = MagicMock(spec=OrderRepo)
        orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
        repo.get_all_active.return_value = orders

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = repo

        handler = OrderInfoHandler(uow)
        result = handler.handle()
        
        assert result == orders

    def test_handle_returns_empty_list(self):
        repo = MagicMock(spec=OrderRepo)
        repo.get_all_active.return_value = None

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = repo

        handler = OrderInfoHandler(uow)
        assert handler.handle() == []
import pytest
from unittest.mock import MagicMock
from cafe_manager.application.use_cases.kitchen_handlers import (
    KitchenStartHandler,
    KitchenListPending,
    KitchenReadyHandler,
)
from cafe_manager.common.exceptions import (
    CoffeeMachineNotFoundError,
    EmployeeNotFoundError,
    KitchenOverloadError,
    OrderNotFoundError,
)
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.entities.people import Employee
from cafe_manager.domain.entities.equipment import CoffeeMachine
from cafe_manager.domain.entities.menu import MenuItem, MenuItemCategory
from cafe_manager.domain.services.ingredient_calculator import IngredientCalculator
from cafe_manager.application.interfaces import (
    CoffeeMachineRepo,
    EmployeeRepo,
    InventoryRepo,
    OrderRepo,
)



class TestKitchenStartHandler:
    @pytest.fixture
    def mock_deps(self):
        order_repo = MagicMock(spec=OrderRepo)
        employee_repo = MagicMock(spec=EmployeeRepo)
        inventory_repo = MagicMock(spec=InventoryRepo)
        machine_repo = MagicMock(spec=CoffeeMachineRepo)
        ingredient_calculator = MagicMock(spec=IngredientCalculator)

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = order_repo
        uow.employee_repo = employee_repo
        uow.inventory_repo = inventory_repo
        uow.machine_repo = machine_repo

        return {
            "uow": uow,
            "order_repo": order_repo,
            "employee_repo": employee_repo,
            "inventory_repo": inventory_repo,
            "machine_repo": machine_repo,
            "ingredient_calculator": ingredient_calculator,
        }

    def test_handle_no_orders(self, mock_deps):
        mock_deps["order_repo"].get_oldest_paid.return_value = None
        handler = KitchenStartHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
        )
        
        result = handler.handle(None)
        assert result == (None, None, None)

    def test_handle_success_no_coffee(self, mock_deps):
        order = MagicMock(spec=Order)
        order.order_id = "ord-1"
        order.employee_id = "emp-1"
        order.machine_id = None
        
        item = MagicMock(spec=MenuItem)
        item.requires_coffee_machine = False
        order.items = {item: 1}
        
        employee = MagicMock(spec=Employee)
        employee.employee_id = "emp-1"
        
        mock_deps["order_repo"].get_oldest_paid.return_value = order
        mock_deps["employee_repo"].get_most_free.return_value = employee
        mock_deps["ingredient_calculator"].calculate.return_value = {"beans": 10}
        
        handler = KitchenStartHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
        )
        order_id, emp_id, mach_id = handler.handle(None)
        
        assert order_id == "ord-1"
        assert emp_id == "emp-1"
        assert mach_id is None
        
        employee.work.assert_called_once()
        order.start_cooking.assert_called_once_with("emp-1")
        mock_deps["inventory_repo"].withdraw.assert_called_once_with({"beans": 10})

    def test_handle_success_with_coffee(self, mock_deps):
        order = MagicMock(spec=Order)
        order.order_id = "ord-coffee"
        order.employee_id = "emp-1"
        
        item = MagicMock(spec=MenuItem)
        item.requires_coffee_machine = True
        order.items = {item: 1}
        
        employee = MagicMock(spec=Employee)
        employee.employee_id = "emp-1"
        
        machine = MagicMock(spec=CoffeeMachine)
        machine.machine_id = 777
        order.machine_id = 777
        
        mock_deps["order_repo"].get_oldest_paid.return_value = order
        mock_deps["employee_repo"].get_most_free.return_value = employee
        mock_deps["machine_repo"].get_free.return_value = machine
        mock_deps["ingredient_calculator"].calculate.return_value = {}
        
        handler = KitchenStartHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
        )
        order_id, emp_id, mach_id = handler.handle(None)
        
        assert mach_id == 777
        machine.start.assert_called_once()
        mock_deps["machine_repo"].save.assert_called_once_with(machine)

    def test_handle_specific_employee_not_found(self, mock_deps):
        mock_deps["order_repo"].get_oldest_paid.return_value = MagicMock(spec=Order)
        mock_deps["employee_repo"].get_by_id.return_value = None
        
        handler = KitchenStartHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
        )
        with pytest.raises(EmployeeNotFoundError):
            handler.handle("emp-ghost")

    def test_handle_all_employees_busy(self, mock_deps):
        mock_deps["order_repo"].get_oldest_paid.return_value = MagicMock(spec=Order)
        mock_deps["employee_repo"].get_most_free.return_value = None
        
        handler = KitchenStartHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
        )
        with pytest.raises(KitchenOverloadError) as exc:
            handler.handle(None)
        assert "employees are busy" in str(exc.value)

    def test_handle_coffee_machine_overload(self, mock_deps):
        order = MagicMock(spec=Order)
        item = MagicMock(spec=MenuItem)
        item.requires_coffee_machine = True
        order.items = {item: 1}
        
        employee = MagicMock(spec=Employee)
        employee.employee_id = "emp-1"
        
        mock_deps["order_repo"].get_oldest_paid.return_value = order
        mock_deps["employee_repo"].get_most_free.return_value = employee
        mock_deps["machine_repo"].get_free.return_value = None
        mock_deps["ingredient_calculator"].calculate.return_value = {}
        
        handler = KitchenStartHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
        )
        with pytest.raises(KitchenOverloadError) as exc:
            handler.handle(None)
        assert "coffee-machines are busy" in str(exc.value)

    def test_handle_specific_employee_success(self, mock_deps):
        order = MagicMock(spec=Order)
        order.order_id = "ord-spec"
        item = MagicMock(spec=MenuItem)
        item.requires_coffee_machine = False
        order.items = {item: 1}
        order.machine_id = None
        
        employee = MagicMock(spec=Employee)
        employee.employee_id = "emp-5"
        order.employee_id = "emp-5"
        
        mock_deps["order_repo"].get_oldest_paid.return_value = order
        mock_deps["employee_repo"].get_by_id.return_value = employee
        mock_deps["ingredient_calculator"].calculate.return_value = {}
        
        handler = KitchenStartHandler(
            uow=mock_deps["uow"],
            ingredient_calculator=mock_deps["ingredient_calculator"],
        )
        handler.handle("emp-5")
        
        mock_deps["employee_repo"].get_by_id.assert_called_once_with("emp-5")
        order.start_cooking.assert_called_once_with("emp-5")


class TestKitchenListPending:
    def test_handle_returns_orders(self):
        repo = MagicMock(spec=OrderRepo)
        orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
        repo.get_paid_from_oldest.return_value = orders

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = repo
        handler = KitchenListPending(uow)
        assert handler.handle() == orders

    def test_handle_returns_empty_list(self):
        repo = MagicMock(spec=OrderRepo)
        repo.get_paid_from_oldest.return_value = None

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = repo
        handler = KitchenListPending(uow)
        assert handler.handle() == []


class TestKitchenReadyHandler:
    @pytest.fixture
    def mock_repos(self, mocker):
        order_repo = mocker.MagicMock()
        machine_repo = mocker.MagicMock()
        uow = mocker.MagicMock()
        uow.__enter__.return_value = uow
        uow.order_repo = order_repo
        uow.machine_repo = machine_repo

        return {
            "uow": uow,
            "order_repo": order_repo,
            "machine_repo": machine_repo,
        }

    def test_handle_success_no_machine(self, mocker, mock_repos):
        order_repo = mock_repos["order_repo"]
        machine_repo = mock_repos["machine_repo"]
        handler = KitchenReadyHandler(mock_repos["uow"])

        mock_order = mocker.MagicMock()
        mock_order.machine_id = None
        order_repo.get_by_id.return_value = mock_order

        handler.handle("ord-123")

        mock_order.end_cooking.assert_called_once()
        order_repo.save.assert_called_once_with(mock_order)
        machine_repo.get_by_id.assert_not_called()
        machine_repo.save.assert_not_called()

    def test_handle_success_with_machine(self, mocker, mock_repos):
        order_repo = mock_repos["order_repo"]
        machine_repo = mock_repos["machine_repo"]
        handler = KitchenReadyHandler(mock_repos["uow"])

        mock_order = mocker.MagicMock()
        mock_order.machine_id = 5
        order_repo.get_by_id.return_value = mock_order

        mock_machine = mocker.MagicMock()
        machine_repo.get_by_id.return_value = mock_machine

        handler.handle("ord-123")

        mock_order.end_cooking.assert_called_once()
        mock_machine.stop.assert_called_once()
        
        order_repo.save.assert_called_once_with(mock_order)
        machine_repo.save.assert_called_once_with(mock_machine)

    def test_handle_order_not_found(self, mock_repos):
        order_repo = mock_repos["order_repo"]
        handler = KitchenReadyHandler(mock_repos["uow"])

        order_repo.get_by_id.return_value = None

        with pytest.raises(OrderNotFoundError) as exc:
            handler.handle("fake-id")
        
        assert "Order with ID fake-id was not found" in str(exc.value)

    def test_handle_machine_not_found(self, mocker, mock_repos):
        order_repo = mock_repos["order_repo"]
        machine_repo = mock_repos["machine_repo"]
        handler = KitchenReadyHandler(mock_repos["uow"])

        mock_order = mocker.MagicMock()
        mock_order.machine_id = 99
        order_repo.get_by_id.return_value = mock_order
        
        machine_repo.get_by_id.return_value = None

        with pytest.raises(CoffeeMachineNotFoundError) as exc:
            handler.handle("ord-123")
        
        assert "Coffee-machine with ID 99 was not found" in str(exc.value)
        mock_order.end_cooking.assert_called_once()

import pytest
from unittest.mock import MagicMock
from cafe_manager.application.use_cases.kitchen_handlers import (
    KitchenStartHandler,
    KitchenListPending,
    KitchenReadyHandler,
)
from cafe_manager.common.exceptions import (
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
        return {
            "order_repo": MagicMock(spec=OrderRepo),
            "employee_repo": MagicMock(spec=EmployeeRepo),
            "inventory_repo": MagicMock(spec=InventoryRepo),
            "machine_repo": MagicMock(spec=CoffeeMachineRepo),
            "ingredient_calculator": MagicMock(spec=IngredientCalculator),
        }

    def test_handle_no_orders(self, mock_deps):
        mock_deps["order_repo"].get_oldest_paid.return_value = None
        handler = KitchenStartHandler(**mock_deps)
        
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
        
        handler = KitchenStartHandler(**mock_deps)
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
        
        handler = KitchenStartHandler(**mock_deps)
        order_id, emp_id, mach_id = handler.handle(None)
        
        assert mach_id == 777
        machine.start.assert_called_once()
        mock_deps["machine_repo"].save.assert_called_once_with(machine)

    def test_handle_specific_employee_not_found(self, mock_deps):
        mock_deps["order_repo"].get_oldest_paid.return_value = MagicMock(spec=Order)
        mock_deps["employee_repo"].get_by_id.return_value = None
        
        handler = KitchenStartHandler(**mock_deps)
        with pytest.raises(EmployeeNotFoundError):
            handler.handle("emp-ghost")

    def test_handle_all_employees_busy(self, mock_deps):
        mock_deps["order_repo"].get_oldest_paid.return_value = MagicMock(spec=Order)
        mock_deps["employee_repo"].get_most_free.return_value = None
        
        handler = KitchenStartHandler(**mock_deps)
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
        
        handler = KitchenStartHandler(**mock_deps)
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
        
        handler = KitchenStartHandler(**mock_deps)
        handler.handle("emp-5")
        
        mock_deps["employee_repo"].get_by_id.assert_called_once_with("emp-5")
        order.start_cooking.assert_called_once_with("emp-5")


class TestKitchenListPending:
    def test_handle_returns_orders(self):
        repo = MagicMock(spec=OrderRepo)
        orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
        repo.get_paid_from_oldest.return_value = orders

        handler = KitchenListPending(repo)
        assert handler.handle() == orders

    def test_handle_returns_empty_list(self):
        repo = MagicMock(spec=OrderRepo)
        repo.get_paid_from_oldest.return_value = None

        handler = KitchenListPending(repo)
        assert handler.handle() == []


class TestKitchenReadyHandler:
    def test_handle_success(self):
        repo = MagicMock(spec=OrderRepo)
        order = MagicMock(spec=Order)
        repo.get_by_id.return_value = order

        handler = KitchenReadyHandler(repo)
        handler.handle("ord-123")

        order.end_cooking.assert_called_once()
        repo.save.assert_called_once_with(order)

    def test_handle_order_not_found(self):
        repo = MagicMock(spec=OrderRepo)
        repo.get_by_id.return_value = None

        handler = KitchenReadyHandler(repo)
        with pytest.raises(OrderNotFoundError):
            handler.handle("ghost")

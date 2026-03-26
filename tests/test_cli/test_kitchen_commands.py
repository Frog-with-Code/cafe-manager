import pytest
from typer.testing import CliRunner
from pathlib import Path
from cafe_manager.cli.kitchen_commands import app
from cafe_manager.common.exceptions import (
    EmployeeNotFoundError,
    KitchenOverloadError,
    OrderNotFoundError,
    OrderStateError,
)

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.kitchen_commands"


class TestListPendingCommand:
    def test_list_pending_basic(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenListPending")
        
        mock_order = mocker.MagicMock()
        mock_order.order_id = "ORD-1"
        mock_order.paid_at = "2023-10-10 12:00"
        mock_handler.return_value.handle.return_value = [mock_order]
        
        result = runner.invoke(app, ["list-pending"])
        
        assert result.exit_code == 0
        assert "pending orders" in result.stdout
        assert "ORD-1" in result.stdout
        assert "2023-10-10 12:00" in result.stdout

    def test_list_pending_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenListPending")
        
        mock_order = mocker.MagicMock()
        mock_order.order_id = "ORD-EX"
        mock_order.paid_at = "now"
        mock_order.total_price = "50.0"
        mock_order.table_id = 7
        mock_handler.return_value.handle.return_value = [mock_order]
        
        result = runner.invoke(app, ["list-pending", "--expanded"])
        
        assert result.exit_code == 0
        assert "50.0" in result.stdout
        assert "7" in result.stdout

class TestStartCommand:
    def test_start_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenStartHandler")
        mock_handler.return_value.handle.return_value = ("ORD-123", "EMP-1", "MACH-5")
        
        result = runner.invoke(app, ["start", "--id", "EMP-1"])
        
        assert result.exit_code == 0
        assert "Order with ID ORD-123 was handed over" in result.stdout
        assert "Employee: EMP-1" in result.stdout
        assert "Machine: MACH-5" in result.stdout

    def test_start_no_paid_orders(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenStartHandler")
        mock_handler.return_value.handle.return_value = (None, None, None)
        
        result = runner.invoke(app, ["start"])
        
        assert result.exit_code == 0
        assert "No paid orders" in result.stdout

    def test_start_employee_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenStartHandler")
        mock_handler.return_value.handle.side_effect = EmployeeNotFoundError("Worker not found")
        
        result = runner.invoke(app, ["start", "--id", "missing"])
        
        assert result.exit_code == 1
        assert "Worker not found" in result.stderr

    def test_start_kitchen_overload(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenStartHandler")
        mock_handler.return_value.handle.side_effect = KitchenOverloadError("Too many cooks")
        
        result = runner.invoke(app, ["start"])
        
        assert result.exit_code == 1
        assert "Too many cooks" in result.stderr

class TestCompleteCommand:
    def test_complete_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenReadyHandler")
        
        result = runner.invoke(app, ["complete", "--id", "ORD-123"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("ORD-123")

    def test_complete_order_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenReadyHandler")
        mock_handler.return_value.handle.side_effect = OrderNotFoundError("Missing order")
        
        result = runner.invoke(app, ["complete", "--id", "fake"])
        
        assert result.exit_code == 1
        assert "Missing order" in result.stderr

    def test_complete_state_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.KitchenReadyHandler")
        mock_handler.return_value.handle.side_effect = OrderStateError("Not cooking yet")
        
        result = runner.invoke(app, ["complete", "--id", "ORD-99"])
        
        assert result.exit_code == 1
        assert "Not cooking yet" in result.stderr
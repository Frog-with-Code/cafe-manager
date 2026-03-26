import pytest
from typer.testing import CliRunner
from pathlib import Path
from uuid import uuid4
from cafe_manager.cli.order_commands import app
from cafe_manager.common.exceptions import (
    OrderNotFoundError,
    OrderStateError,
    InsufficientStocksError,
    TableNotFoundError,
    AccountNotFoundError,
)

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.order_commands"


class TestCreateCommand:
    def test_create_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderCreateHandler")
        mock_handler.return_value.handle.return_value = "order_123"

        result = runner.invoke(app, ["create", "espresso:2", "latte:1", "--table", "5"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(
            [("espresso", 2), ("latte", 1)], 5, False
        )
        assert "New order with ID order_123 was created" in result.stdout

    def test_create_invalid_format(self, mocker):
        result = runner.invoke(app, ["create", "invalid_item"])
        assert result.exit_code != 0
        assert "Format invalid_item is incorrect" in result.stderr

    def test_create_insufficient_stocks(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderCreateHandler")
        mock_handler.return_value.handle.side_effect = InsufficientStocksError(
            "No beans"
        )

        result = runner.invoke(app, ["create", "espresso:1"])

        assert result.exit_code == 1
        assert "No beans" in result.stderr


class TestPayCommand:
    def test_pay_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderPayHandler")

        result = runner.invoke(app, ["pay", "--id", "order_123", "--price", "50.5"])

        assert result.exit_code == 0
        assert "Order was paid" in result.stdout

    def test_pay_order_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderPayHandler")
        mock_handler.return_value.handle.side_effect = OrderNotFoundError("Order 404")

        result = runner.invoke(app, ["pay", "--id", "none", "--price", "10"])

        assert result.exit_code == 1
        assert "Order 404" in result.stderr

    def test_pay_account_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderPayHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError(
            "Bank error"
        )

        result = runner.invoke(
            app, ["pay", "--id", "id", "--price", "10", "--account", str(uuid4())]
        )

        assert result.exit_code == 1
        assert "Bank error" in result.stderr


class TestInfoCommand:
    def test_info_basic(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderInfoHandler")
        mock_order = mocker.MagicMock()
        mock_order.order_id = "ORD-1"
        mock_order._state = "PAID"
        mock_handler.return_value.handle.return_value = [mock_order]

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "active orders" in result.stdout
        assert "ORD-1" in result.stdout
        assert "PAID" in result.stdout

    def test_info_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderInfoHandler")
        mock_order = mocker.MagicMock()
        mock_order.order_id = "ORD-EX"
        mock_order._state = "COOKING"
        mock_order.total_price = "15.0"
        mock_handler.return_value.handle.return_value = [mock_order]

        result = runner.invoke(app, ["info", "--expanded"])

        assert result.exit_code == 0
        assert "ORD-EX" in result.stdout
        assert "15.0" in result.stdout


class TestServeCommand:
    def test_serve_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderServeHandler")

        result = runner.invoke(app, ["serve", "--id", "order_777"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("order_777")
        assert "Order was served" in result.stdout

    def test_serve_invalid_state(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.OrderServeHandler")
        mock_handler.return_value.handle.side_effect = OrderStateError("Not ready yet")

        result = runner.invoke(app, ["serve", "--id", "order_000"])

        assert result.exit_code == 1
        assert "Not ready yet" in result.stderr

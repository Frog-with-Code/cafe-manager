import pytest
from typer.testing import CliRunner
from pathlib import Path
from uuid import uuid4
from cafe_manager.cli.table_commands import app
from cafe_manager.common.exceptions import (
    TableNotFoundError,
    InsufficientBudgetError,
    TableSuitableNotFoundError,
    TableBusyError,
    TablePlacesError,
    AccountNotFoundError,
)

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.table_commands"


class TestBuyCommand:
    def test_buy_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableBuyHandler")

        result = runner.invoke(app, ["buy", "--price", "1000", "--seats", "4"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()
        assert "New 4-seats table was bought" in result.stdout

    def test_buy_insufficient_budget(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableBuyHandler")
        mock_handler.return_value.handle.side_effect = InsufficientBudgetError(
            "No money"
        )

        result = runner.invoke(app, ["buy", "--price", "99999", "--seats", "2"])

        assert result.exit_code == 1
        assert "No money" in result.stderr


class TestDiscardCommand:
    def test_discard_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableDiscardHandler")

        result = runner.invoke(app, ["discard", "--id", "1", "--force"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(1)
        assert "Table '1' was discarded" in result.stdout

    def test_discard_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableDiscardHandler")
        mock_handler.return_value.handle.side_effect = TableNotFoundError(
            "Table missing"
        )

        result = runner.invoke(app, ["discard", "--id", "99", "--force"])

        assert result.exit_code == 1
        assert "Table missing" in result.stderr


class TestInfoCommand:
    def test_info_basic(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableInfoHandler")

        mock_table = mocker.MagicMock()
        mock_table.table_id = 5
        mock_handler.return_value.handle.return_value = [mock_table]

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "tables" in result.stdout
        assert "5" in result.stdout

    def test_info_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableInfoHandler")

        mock_table = mocker.MagicMock()
        mock_table.table_id = 5
        mock_table.max_places = 4
        mock_table.chairs_amount = 4
        mock_table._state = "available"
        mock_handler.return_value.handle.return_value = [mock_table]

        result = runner.invoke(app, ["info", "--expanded"])

        assert result.exit_code == 0
        assert "available" in result.stdout
        assert "capacity" in result.stdout


class TestReserveCommand:
    def test_reserve_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableReserveHandler")
        mock_handler.return_value.handle.return_value = 10

        result = runner.invoke(app, ["reserve", "--seats", "4"])

        assert result.exit_code == 0
        assert "Table with ID 10 was reserved" in result.stdout

    def test_reserve_no_suitable_table(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableReserveHandler")
        mock_handler.return_value.handle.side_effect = TableSuitableNotFoundError(
            "No tables"
        )

        result = runner.invoke(app, ["reserve", "--seats", "100"])

        assert result.exit_code == 1
        assert "No tables" in result.stderr


class TestFreeCommand:
    def test_free_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableFreeHandler")

        result = runner.invoke(app, ["free", "--id", "5"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(5)
        assert "Table with ID 5 was freed" in result.stdout

    def test_free_busy_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.TableFreeHandler")
        mock_handler.return_value.handle.side_effect = TableBusyError("Orders unpaid")

        result = runner.invoke(app, ["free", "--id", "5"])

        assert result.exit_code == 1
        assert "Orders unpaid" in result.stderr


class TestAssignChairCommand:
    def test_assign_chair_success(self, mocker):
        mocker.patch(f"{PATCH_TARGET}.init_context", return_value=None)
        mocker.patch(f"{PATCH_TARGET}.get_uow", return_value=mocker.MagicMock())
        mock_handler = mocker.patch(f"{PATCH_TARGET}.AssignChairToTableHandler")

        result = runner.invoke(app, ["assign-chair", "--table", "1", "--chair", "10"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(
            table_id=1, chair_id=10
        )
        assert "Chair 10 was assigned to table 1" in result.stdout

    def test_assign_chair_limit_reached(self, mocker):
        mocker.patch(f"{PATCH_TARGET}.init_context", return_value=None)
        mocker.patch(f"{PATCH_TARGET}.get_uow", return_value=mocker.MagicMock())
        mock_handler = mocker.patch(f"{PATCH_TARGET}.AssignChairToTableHandler")
        mock_handler.return_value.handle.side_effect = TablePlacesError(
            "No room for more chairs"
        )

        result = runner.invoke(app, ["assign-chair", "--table", "1", "--chair", "2"])

        assert result.exit_code == 1
        assert "No room for more chairs" in result.stderr

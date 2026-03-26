import pytest
from typer.testing import CliRunner
from pathlib import Path
from uuid import uuid4
from cafe_manager.cli.chair_commands import app
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    InsufficientBudgetError,
    ChairNotFoundError,
    TableNotFoundError,
)

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.chair_commands"

class TestBuyCommand:
    def test_buy_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairBuyHandler")
        mocker.patch(f"{PATCH_TARGET}.SQLiteChairRepo")
        mocker.patch(f"{PATCH_TARGET}.SQLiteFinanceRepo")
        
        result = runner.invoke(app, ["buy", "--price", "500"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()
        assert "New chair was bought" in result.stdout

    def test_buy_insufficient_budget(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairBuyHandler")
        mock_handler.return_value.handle.side_effect = InsufficientBudgetError("Not enough money")
        
        result = runner.invoke(app, ["buy", "--price", "1000000"])
        
        assert result.exit_code == 1
        assert "Not enough money" in result.stderr

    def test_buy_account_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairBuyHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError("Account missing")
        account_id = str(uuid4())
        
        result = runner.invoke(app, ["buy", "--price", "500", "--account", account_id])
        
        assert result.exit_code == 1
        assert "Account missing" in result.stderr


class TestDiscardCommand:
    def test_discard_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairDiscardHandler")
        mocker.patch(f"{PATCH_TARGET}.SQLiteChairRepo")
        mocker.patch(f"{PATCH_TARGET}.SQLiteTableRepo")
        
        result = runner.invoke(app, ["discard", "--id", "1"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(1)
        assert "Chair with ID 1 was discarded" in result.stdout

    def test_discard_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairDiscardHandler")
        mock_handler.return_value.handle.side_effect = ChairNotFoundError("Chair not found")
        
        result = runner.invoke(app, ["discard", "--id", "999"])
        
        assert result.exit_code == 1
        assert "Chair not found" in result.stderr

    def test_discard_table_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairDiscardHandler")
        mock_handler.return_value.handle.side_effect = TableNotFoundError("Table context error")
        
        result = runner.invoke(app, ["discard", "--id", "1"])
        
        assert result.exit_code == 1
        assert "Table context error" in result.stderr


class TestInfoCommand:
    def test_info_basic(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairInfoHandler")
        mocker.patch(f"{PATCH_TARGET}.SQLiteChairRepo")
        
        mock_chair = mocker.MagicMock()
        mock_chair.chair_id = 101
        mock_handler.return_value.handle.return_value = [mock_chair]
        
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "chairs" in result.stdout
        assert "101" in result.stdout

    def test_info_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairInfoHandler")
        
        mock_chair = mocker.MagicMock()
        mock_chair.chair_id = 101
        mock_chair._state = "FREE"
        mock_chair._table_id = 5
        mock_handler.return_value.handle.return_value = [mock_chair]
        
        result = runner.invoke(app, ["info", "--expended"])
        
        assert result.exit_code == 0
        assert "FREE" in result.stdout
        assert "5" in result.stdout

    def test_info_empty(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ChairInfoHandler")
        mock_handler.return_value.handle.return_value = []
        
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert result.stdout.strip() == ""
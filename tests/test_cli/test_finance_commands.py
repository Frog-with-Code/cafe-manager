import pytest
from typer.testing import CliRunner
from pathlib import Path
from uuid import uuid4
from cafe_manager.cli.finance_commands import app
from cafe_manager.common.exceptions import AccountNotFoundError

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.finance_commands"


class TestInvestCommand:
    def test_invest_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceInvestHandler")

        result = runner.invoke(
            app, ["invest", "--money", "1000", "--description", "Test Investment"]
        )

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()

    def test_invest_account_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceInvestHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError(
            "Account not found"
        )

        result = runner.invoke(
            app, ["invest", "--money", "500", "--description", str(uuid4())]
        )

        assert result.exit_code == 1
        assert "Account not found" in result.stderr


class TestStatsCommand:
    def test_stats_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceStatsHandler")
        mock_handler.return_value.handle.return_value = {
            "id": "uuid-123",
            "balance": "1000.00",
            "income": "1500.00",
            "expense": "500.00",
            "is_loss": False,
            "profit_abs": "1000.00",
        }

        result = runner.invoke(app, ["stats"])

        assert result.exit_code == 0
        assert "ID:" in result.stdout
        assert "Balance:" in result.stdout
        assert "1000.00" in result.stdout
        assert "+1000.00" in result.stdout

    def test_stats_account_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceStatsHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError(
            "Account missing"
        )

        result = runner.invoke(app, ["stats", "--account", str(uuid4())])

        assert result.exit_code == 1
        assert "Account missing" in result.stderr


class TestHistoryCommand:
    def test_history_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceHistoryHandler")

        mock_tx = mocker.MagicMock()
        mock_tx.money = "100.00"
        mock_tx.transaction_type = "INCOME"
        mock_handler.return_value.handle.return_value = [mock_tx]

        result = runner.invoke(app, ["history", "--limit", "5"])

        assert result.exit_code == 0
        assert "history" in result.stdout
        assert "100.00" in result.stdout
        assert "INCOME" in result.stdout

    def test_history_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceHistoryHandler")

        mock_tx = mocker.MagicMock()
        mock_tx.money = "20.00"
        mock_tx.transaction_type = "EXPENSE"
        mock_tx.transaction_id = "tx-123"
        mock_tx.time = "2023-10-10 10:00"
        mock_tx.description = "Buying milk"
        mock_handler.return_value.handle.return_value = [mock_tx]

        result = runner.invoke(app, ["history", "--expanded"])

        assert result.exit_code == 0
        assert "tx-123" in result.stdout
        assert "Buying milk" in result.stdout

    def test_history_account_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceHistoryHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError(
            "No history"
        )

        result = runner.invoke(app, ["history", "--account", str(uuid4())])

        assert result.exit_code == 1
        assert "No history" in result.stderr


class TestSetPrimaryCommand:
    def test_set_primary_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceSetPrimaryHandler")
        acc_id = str(uuid4())

        result = runner.invoke(app, ["set-primary", acc_id])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()

    def test_set_primary_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.FinanceSetPrimaryHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError(
            "Invalid UUID"
        )

        result = runner.invoke(app, ["set-primary", str(uuid4())])

        assert result.exit_code == 1
        assert "Invalid UUID" in result.stderr

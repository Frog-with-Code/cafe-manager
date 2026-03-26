import pytest
from typer.testing import CliRunner
from pathlib import Path
from uuid import uuid4
from cafe_manager.cli.machine_commands import app
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CoffeeMachineNotFoundError,
    CoffeeMachineStateError,
    InsufficientBudgetError,
)

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.machine_commands"


class TestBuyCommand:
    def test_buy_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineBuyHandler")

        result = runner.invoke(
            app, ["buy", "--price", "5000", "--model", "DeLonghi", "--limit", "500"]
        )

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()
        assert "Coffee-machine of model 'DeLonghi' was bought" in result.stdout

    def test_buy_insufficient_budget(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineBuyHandler")
        mock_handler.return_value.handle.side_effect = InsufficientBudgetError(
            "Not enough funds"
        )

        result = runner.invoke(app, ["buy", "--price", "99999", "--model", "RichModel"])

        assert result.exit_code == 1
        assert "Not enough funds" in result.stderr

    def test_buy_account_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineBuyHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError(
            "Account missing"
        )

        result = runner.invoke(
            app, ["buy", "--price", "100", "--model", "M", "--account", str(uuid4())]
        )

        assert result.exit_code == 1
        assert "Account missing" in result.stderr


class TestDiscardCommand:
    def test_discard_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineDiscardHandler")

        result = runner.invoke(app, ["discard", "--id", "1", "--force"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(1)
        assert "Coffee-machine with ID 1 was discarded" in result.stdout

    def test_discard_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineDiscardHandler")
        mock_handler.return_value.handle.side_effect = CoffeeMachineNotFoundError(
            "Machine 404"
        )

        result = runner.invoke(app, ["discard", "--id", "99", "--force"])

        assert result.exit_code == 1
        assert "Machine 404" in result.stderr


class TestInfoCommand:
    def test_info_basic(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineInfoHandler")

        mock_machine = mocker.MagicMock()
        mock_machine.machine_id = 10
        mock_handler.return_value.handle.return_value = [mock_machine]

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "coffee-machines" in result.stdout
        assert "10" in result.stdout

    def test_info_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineInfoHandler")

        mock_machine = mocker.MagicMock()
        mock_machine.machine_id = 10
        mock_machine.model = "X-Series"
        mock_machine._state = "READY"
        mock_machine.maintenance_limit = 1000
        mock_machine.cycles_count = 50
        mock_handler.return_value.handle.return_value = [mock_machine]

        result = runner.invoke(app, ["info", "--expanded"])

        assert result.exit_code == 0
        assert "X-Series" in result.stdout
        assert "READY" in result.stdout
        assert "1000" in result.stdout
        assert "50" in result.stdout


class TestServiceCommand:
    def test_service_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineServiceHandler")

        result = runner.invoke(app, ["service", "--id", "5"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(5)
        assert "Coffee-machine with ID 5 was given for maintenance" in result.stdout

    def test_service_state_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineServiceHandler")
        mock_handler.return_value.handle.side_effect = CoffeeMachineStateError(
            "Already in service"
        )

        result = runner.invoke(app, ["service", "--id", "5"])

        assert result.exit_code == 1
        assert "Already in service" in result.stderr


class TestResumeCommand:
    def test_resume_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineResumeHandler")

        result = runner.invoke(app, ["resume", "--id", "5"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with(5)
        assert "Coffee-machine with ID 5 was taken from maintenance" in result.stdout

    def test_resume_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CoffeeMachineResumeHandler")
        mock_handler.return_value.handle.side_effect = CoffeeMachineNotFoundError(
            "Not found"
        )

        result = runner.invoke(app, ["resume", "--id", "999"])

        assert result.exit_code == 1
        assert "Not found" in result.stderr

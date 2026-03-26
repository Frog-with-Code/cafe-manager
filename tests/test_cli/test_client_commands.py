import pytest
from typer.testing import CliRunner
from pathlib import Path
from cafe_manager.cli.client_commands import app
from cafe_manager.common.exceptions import ClientNotFoundError

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.client_commands"


class TestCreateCommand:
    def test_create_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ClientCreateHandler")
        mock_handler.return_value.handle.return_value = "client-uuid-123"

        result = runner.invoke(app, ["create", "--name", "John Doe"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("John Doe")
        assert "New client with ID 'client-uuid-123' was created" in result.stdout

    def test_create_runtime_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ClientCreateHandler")
        mock_handler.return_value.handle.side_effect = RuntimeError("Database is full")

        result = runner.invoke(app, ["create", "--name", "John Doe"])

        assert result.exit_code == 1
        assert "Database is full" in result.stderr


class TestInfoCommand:
    def test_info_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ClientInfoHandler")

        mock_client = mocker.MagicMock()
        mock_client.client_id = "client-123"
        mock_client.name = "John Doe"
        mock_client.total_spent = "150.00"
        mock_client.orders_amount = 5
        mock_client.registered_at = "2023-01-01"

        mock_handler.return_value.handle.return_value = mock_client

        result = runner.invoke(app, ["info", "--id", "client-123"])

        assert result.exit_code == 0
        assert "client-123" in result.stdout
        assert "John Doe" in result.stdout
        assert "150.00" in result.stdout
        assert "5" in result.stdout
        assert "2023-01-01" in result.stdout

    def test_info_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.ClientInfoHandler")
        mock_handler.return_value.handle.side_effect = ClientNotFoundError(
            "Client not found"
        )

        result = runner.invoke(app, ["info", "--id", "missing-id"])

        assert result.exit_code == 1
        assert "Client not found" in result.stderr

import pytest
from typer.testing import CliRunner
from pathlib import Path
from cafe_manager.cli.cafe_commands import app
from cafe_manager.common.exceptions import CafeEnvNameError
from cafe_manager.application.use_cases.cafe_handlers import (
    CafeEnvNotFoundError,
    CafeEnvNoActiveError,
    CafeEnvAlreadyInitError,
    CafeEnvExistsError
)

runner = CliRunner()

PATCH_TARGET = "cafe_manager.cli.cafe_commands"

class TestCreateCommand:
    def test_create_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeCreateHandler")
        result = runner.invoke(app, ["create", "--name", "new_cafe"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("new_cafe")
        assert "created" in result.stdout

    def test_create_business_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeCreateHandler")
        mock_handler.return_value.handle.side_effect = CafeEnvNameError("Invalid name")
        result = runner.invoke(app, ["create", "--name", "!!!"])
        
        assert result.exit_code == 1
        assert "Invalid name" in result.stderr

class TestRemoveCommand:
    def test_remove_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeRemoveHandler")
        result = runner.invoke(app, ["remove", "--name", "old_cafe", "--force"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("old_cafe")
        assert "deleted" in result.stdout

    def test_remove_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeRemoveHandler")
        mock_handler.return_value.handle.side_effect = CafeEnvNotFoundError("Not found")
        result = runner.invoke(app, ["remove", "--name", "missing", "--force"])
        
        assert result.exit_code == 1
        assert "Not found" in result.stderr

class TestActivateCommand:
    def test_activate_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeActivateHandler")
        result = runner.invoke(app, ["activate", "--name", "target_cafe"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("target_cafe")
        assert "activated" in result.stdout

    def test_activate_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeActivateHandler")
        mock_handler.return_value.handle.side_effect = CafeEnvNoActiveError("Error")
        result = runner.invoke(app, ["activate", "--name", "target_cafe"])
        
        assert result.exit_code == 1

class TestDeactivateCommand:
    def test_deactivate_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeDeactivateHandler")
        result = runner.invoke(app, ["deactivate"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()
        assert "deactivated" in result.stdout

    def test_deactivate_silent_exception(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeDeactivateHandler")
        mock_handler.return_value.handle.side_effect = CafeEnvNoActiveError("No active")
        result = runner.invoke(app, ["deactivate"])
        
        assert result.exit_code == 0

class TestInitCommand:
    def test_init_success(self, mocker):
        mocker.patch(f"{PATCH_TARGET}.init_context", side_effect=lambda ctx: setattr(ctx, 'obj', {'active_env': Path("cafe.db")}))
        mocker.patch(f"{PATCH_TARGET}.SQLiteCafeRepo")
        mocker.patch(f"{PATCH_TARGET}.SQLiteFinanceRepo")
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeInitHandler")
        
        result = runner.invoke(app, ["init", "--name", "Cafe", "--address", "Addr", "--capital", "1000"])
        
        assert result.exit_code == 0
        assert "initialized" in result.stdout

    def test_init_already_initialized(self, mocker):
        mocker.patch(f"{PATCH_TARGET}.init_context", side_effect=lambda ctx: setattr(ctx, 'obj', {'active_env': Path("cafe.db")}))
        mock_handler = mocker.patch(f"{PATCH_TARGET}.CafeInitHandler")
        mock_handler.return_value.handle.side_effect = CafeEnvAlreadyInitError("Already init")
        
        result = runner.invoke(app, ["init", "--name", "C", "--address", "A"])
        
        assert result.exit_code == 1
        assert "Already init" in result.stderr

class TestListCommand:
    def test_list_output(self, mocker):
        mock_env_manager = mocker.patch(f"{PATCH_TARGET}.env_manager")
        mock_base_dir = mocker.patch(f"{PATCH_TARGET}.BASE_DIR")
        
        mock_db = mocker.MagicMock(spec=Path)
        mock_db.stem = "my_cafe"
        mock_db.suffix = ".db"
        mock_db.resolve.return_value = "/path/my_cafe.db"
        mock_db.name = "my_cafe.db"
        
        mock_base_dir.glob.return_value = [mock_db]
        mock_env_manager.get_active_env_path.return_value = mock_db
        
        result = runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "my_cafe" in result.stdout
        assert "/path/my_cafe.db" in result.stdout
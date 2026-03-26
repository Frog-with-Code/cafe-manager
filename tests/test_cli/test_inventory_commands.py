import pytest
from typer.testing import CliRunner
from pathlib import Path
from uuid import uuid4
from cafe_manager.cli.inventory_commands import app
from cafe_manager.common.exceptions import (
    IngredientExistsError,
    IngredientNotFoundError,
    InsufficientBudgetError,
    AccountNotFoundError,
)

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.inventory_commands"


class TestAddIngredientCommand:
    def test_add_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventoryAddHandler")
        
        result = runner.invoke(app, ["add-ingredient", "--name", "Milk", "--unit", "ml"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("Milk", "ml", False)
        assert "'Milk' was added to the inventory" in result.stdout

    def test_add_already_exists(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventoryAddHandler")
        mock_handler.return_value.handle.side_effect = IngredientExistsError("Ingredient already exists")
        
        result = runner.invoke(app, ["add-ingredient", "--name", "Milk", "--unit", "ml"])
        
        assert result.exit_code == 1
        assert "Ingredient already exists" in result.stderr

class TestRemoveIngredientCommand:
    def test_remove_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventoryRemoveHandler")
        
        result = runner.invoke(app, ["remove-ingredient", "--name", "Coffee Beans"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("Coffee Beans")
        assert "'Coffee Beans' was removed from the inventory" in result.stdout

    def test_remove_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventoryRemoveHandler")
        mock_handler.return_value.handle.side_effect = IngredientNotFoundError("Not found")
        
        result = runner.invoke(app, ["remove-ingredient", "--name", "Sugar"])
        
        assert result.exit_code == 1
        assert "Not found" in result.stderr

class TestInfoCommand:
    def test_info_basic(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventoryInfoHandler")
        
        mock_ing = mocker.MagicMock()
        mock_ing.name = "Milk"
        mock_handler.return_value.handle.return_value = {mock_ing: 10.0}
        
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "ingredients" in result.stdout
        assert "Milk" in result.stdout

    def test_info_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventoryInfoHandler")
        
        mock_ing = mocker.MagicMock()
        mock_ing.name = "Milk"
        mock_ing.unit = "LITER"
        mock_handler.return_value.handle.return_value = {mock_ing: 10.0}
        
        result = runner.invoke(app, ["info", "--expanded"])
        
        assert result.exit_code == 0
        assert "Milk" in result.stdout
        assert "10.0" in result.stdout
        assert "LITER" in result.stdout

class TestSupplyCommand:
    def test_supply_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventorySupplyHandler")
        
        result = runner.invoke(app, ["supply", "--name", "Milk", "--quantity", "5", "--price", "100", "--force"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()
        assert "Inventory was supplied by 'Milk'" in result.stdout

    def test_supply_ingredient_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventorySupplyHandler")
        mock_handler.return_value.handle.side_effect = IngredientNotFoundError("Unknown ingredient")
        
        result = runner.invoke(app, ["supply", "-n", "Gold", "-q", "1", "-p", "1000", "--force"])
        
        assert result.exit_code == 1
        assert "Unknown ingredient" in result.stderr

    def test_supply_insufficient_budget(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventorySupplyHandler")
        mock_handler.return_value.handle.side_effect = InsufficientBudgetError("Poor cafe")
        
        result = runner.invoke(app, ["supply", "-n", "Milk", "-q", "100", "-p", "99999", "--force"])
        
        assert result.exit_code == 1
        assert "Poor cafe" in result.stderr

    def test_supply_account_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.InventorySupplyHandler")
        mock_handler.return_value.handle.side_effect = AccountNotFoundError("Bank error")
        
        result = runner.invoke(app, ["supply", "-n", "Milk", "-q", "1", "-p", "10", "--account", str(uuid4()), "--force"])
        
        assert result.exit_code == 1
        assert "Bank error" in result.stderr
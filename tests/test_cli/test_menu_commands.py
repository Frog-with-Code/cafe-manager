import pytest
from typer.testing import CliRunner
from pathlib import Path
from cafe_manager.cli.menu_commands import app
from cafe_manager.common.exceptions import (
    MenuItemExistsError,
    MenuItemNotFoundError,
)

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.menu_commands"


class TestInfoCommand:
    def test_info_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.MenuInfoHandler")

        mock_item = mocker.MagicMock()
        mock_item.name = "Espresso"
        mock_item.price = "2.5"
        mock_item.category = "COFFEE"

        mock_handler.return_value.handle.return_value = {"COFFEE": [mock_item]}

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "COFFEE" in result.stdout
        assert "Espresso" in result.stdout

    def test_info_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.MenuInfoHandler")

        mock_item = mocker.MagicMock()
        mock_item.name = "Espresso"
        mock_item.price = "2.5"
        mock_item.category = "COFFEE"

        mock_handler.return_value.handle.return_value = {"COFFEE": [mock_item]}

        result = runner.invoke(app, ["info", "--expanded"])

        assert result.exit_code == 0
        assert "Espresso" in result.stdout
        assert "2.5" in result.stdout
        assert "COFFEE" in result.stdout


class TestAddItemCommand:
    def test_add_item_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.MenuAddItemHandler")

        user_input = "Coffee\n10.0\nq\n"

        result = runner.invoke(
            app,
            ["add-item", "--name", "Latte", "--price", "5.0", "--category", "coffee"],
            input=user_input,
        )

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once()
        assert "Latte was added to the menu" in result.stdout

    def test_add_item_already_exists(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.MenuAddItemHandler")
        mock_handler.return_value.handle.side_effect = MenuItemExistsError(
            "Menu item exists"
        )

        user_input = "Coffee\n5\nq\n"
        result = runner.invoke(
            app,
            ["add-item", "--name", "Latte", "--price", "5", "--category", "coffee"],
            input=user_input,
        )

        assert result.exit_code == 1
        assert "Menu item exists" in result.stderr

    def test_add_item_no_ingredients(self, mocker):
        user_input = "q\n"

        result = runner.invoke(
            app,
            ["add-item", "--name", "EmptyItem", "--price", "1", "--category", "coffee"],
            input=user_input,
        )

        assert result.exit_code == 1
        assert "Impossible to add menu item without ingredients" in result.stderr


class TestRemoveItemCommand:
    def test_remove_item_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.MenuItemRemoveHandler")

        result = runner.invoke(app, ["remove-item", "--name", "Espresso"])

        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("Espresso")
        assert "Espresso was removed from the menu" in result.stdout

    def test_remove_item_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.MenuItemRemoveHandler")
        mock_handler.return_value.handle.side_effect = MenuItemNotFoundError(
            "Not found"
        )

        result = runner.invoke(app, ["remove-item", "--name", "Ghost"])

        assert result.exit_code == 1
        assert "Not found" in result.stderr

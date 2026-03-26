import pytest
from unittest.mock import MagicMock
from decimal import Decimal

from cafe_manager.application.use_cases.menu_handlers import (
    MenuInfoHandler,
    MenuAddItemHandler,
    MenuItemRemoveHandler,
)
from cafe_manager.common.exceptions import IngredientNotFoundError, MenuItemExistsError, MenuItemNotFoundError
from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import (
    Ingredient,
    MenuItem,
    MenuItemCategory,
    MenuItemType,
)
from cafe_manager.application.interfaces import InventoryRepo, MenuRepo


class TestMenuInfoHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=MenuRepo)

    def test_handle_returns_empty_dict_on_no_items(self, mock_repo):
        mock_repo.get_all.return_value = None
        handler = MenuInfoHandler(mock_repo)
        assert handler.handle() == {}

    def test_handle_groups_items_by_type(self, mock_repo):
        item_drink = MagicMock(spec=MenuItem)
        item_drink.item_type = MenuItemType.DRINK
        item_food = MagicMock(spec=MenuItem)
        item_food.item_type = MenuItemType.FOOD
        
        mock_repo.get_all.return_value = {item_drink, item_food}
        
        handler = MenuInfoHandler(mock_repo)
        result = handler.handle()
        
        assert len(result) == 2
        assert item_drink in result[MenuItemType.DRINK]
        assert item_food in result[MenuItemType.FOOD]


class TestMenuAddItemHandler:
    @pytest.fixture
    def mock_repos(self, mocker):
        return {
            "menu_repo": mocker.MagicMock(),
            "inventory_repo": mocker.MagicMock()
        }

    def test_handle_success(self, mocker, mock_repos):
        menu_repo = mock_repos["menu_repo"]
        inventory_repo = mock_repos["inventory_repo"]
        handler = MenuAddItemHandler(menu_repo, inventory_repo)

        menu_repo.get_by_name.return_value = None
        
        mock_ing = mocker.MagicMock()
        inventory_repo.get_by_names.return_value = {mock_ing: 10.0}

        handler.handle(
            name="Espresso",
            price=mocker.Mock(),
            category=mocker.Mock(),
            ingredients_data={"Coffee": 10.0},
            overwrite=False
        )

        assert menu_repo.save.called
        args, _ = menu_repo.save.call_args
        saved_item = args[0]
        assert saved_item.name == "Espresso"

    def test_handle_item_exists_no_overwrite(self, mocker, mock_repos):
        menu_repo = mock_repos["menu_repo"]
        handler = MenuAddItemHandler(menu_repo, mock_repos["inventory_repo"])

        menu_repo.get_by_name.return_value = mocker.Mock()

        with pytest.raises(MenuItemExistsError) as exc:
            handler.handle(
                name="Latte",
                price=mocker.Mock(),
                category=mocker.Mock(),
                ingredients_data={},
                overwrite=False
            )
        
        assert "already exists" in str(exc.value)

    def test_handle_overwrite_success(self, mocker, mock_repos):
        menu_repo = mock_repos["menu_repo"]
        inventory_repo = mock_repos["inventory_repo"]
        handler = MenuAddItemHandler(menu_repo, inventory_repo)

        menu_repo.get_by_name.return_value = mocker.Mock()
        mock_ing = mocker.MagicMock()
        inventory_repo.get_by_names.return_value = {mock_ing: 5.0}

        handler.handle(
            name="Latte",
            price=mocker.Mock(),
            category=mocker.Mock(),
            ingredients_data={"Milk": 5.0},
            overwrite=True
        )

        assert menu_repo.save.called

    def test_handle_ingredient_not_found(self, mocker, mock_repos):
        inventory_repo = mock_repos["inventory_repo"]
        handler = MenuAddItemHandler(mock_repos["menu_repo"], inventory_repo)

        mock_repos["menu_repo"].get_by_name.return_value = None
        inventory_repo.get_by_names.return_value = None

        with pytest.raises(IngredientNotFoundError) as exc:
            handler.handle(
                name="Cake",
                price=mocker.Mock(),
                category=mocker.Mock(),
                ingredients_data={"Sugar": 100.0},
                overwrite=False
            )
        
        assert "is unknown" in str(exc.value)

    def test_handle_multiple_ingredients(self, mocker, mock_repos):
        menu_repo = mock_repos["menu_repo"]
        inventory_repo = mock_repos["inventory_repo"]
        handler = MenuAddItemHandler(menu_repo, inventory_repo)

        menu_repo.get_by_name.return_value = None
        
        mock_ing1 = mocker.MagicMock()
        mock_ing2 = mocker.MagicMock()
        
        inventory_repo.get_by_names.side_effect = [
            {mock_ing1: 1.0},
            {mock_ing2: 2.0}
        ]

        handler.handle(
            name="Cappuccino",
            price=mocker.Mock(),
            category=mocker.Mock(),
            ingredients_data={"Coffee": 1.0, "Milk": 2.0},
            overwrite=False
        )

        assert inventory_repo.get_by_names.call_count == 2
        assert menu_repo.save.called


class TestMenuItemRemoveHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=MenuRepo)

    def test_handle_success(self, mock_repo):
        mock_repo.get_by_name.return_value = MagicMock(spec=MenuItem)
        handler = MenuItemRemoveHandler(mock_repo)
        
        handler.handle("Cappuccino")
        mock_repo.delete_by_name.assert_called_once_with("Cappuccino")

    def test_handle_not_found_error(self, mock_repo):
        mock_repo.get_by_name.return_value = None
        handler = MenuItemRemoveHandler(mock_repo)
        
        with pytest.raises(MenuItemNotFoundError):
            handler.handle("Unknown Item")
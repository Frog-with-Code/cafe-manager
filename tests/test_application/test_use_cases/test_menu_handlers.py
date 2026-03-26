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
    def mock_deps(self):
        return {
            "menu_repo": MagicMock(spec=MenuRepo),
            "inventory_repo": MagicMock(spec=InventoryRepo)
        }

    def test_handle_success(self, mock_deps):
        mock_deps["menu_repo"].get_by_name.return_value = None
        
        mock_ingredient = MagicMock(spec=Ingredient)
        mock_deps["inventory_repo"].get_by_names.return_value = mock_ingredient
        
        handler = MenuAddItemHandler(**mock_deps)
        
        ingredients_data = {"Coffee Beans": 18.0}
        price = Money(Decimal("5.00"))
        
        handler.handle(
            name="Espresso",
            price=price,
            category=MenuItemCategory.COFFEE,
            ingredients_data=ingredients_data,
            overwrite=False
        )
        
        mock_deps["menu_repo"].save.assert_called_once()
        saved_item = mock_deps["menu_repo"].save.call_args[0][0]
        assert saved_item.name == "Espresso"
        assert saved_item.price == price
        assert mock_ingredient in saved_item.recipe.ingredients

    def test_handle_already_exists_error(self, mock_deps):
        mock_deps["menu_repo"].get_by_name.return_value = MagicMock(spec=MenuItem)
        
        handler = MenuAddItemHandler(**mock_deps)
        
        with pytest.raises(MenuItemExistsError):
            handler.handle(
                name="Latte",
                price=Money(Decimal("1.0")),
                category=MenuItemCategory.COFFEE,
                ingredients_data={},
                overwrite=False
            )

    def test_handle_overwrite_existing_success(self, mock_deps):
        mock_deps["menu_repo"].get_by_name.return_value = MagicMock(spec=MenuItem)
        mock_deps["inventory_repo"].get_by_names.return_value = MagicMock(spec=Ingredient)
        
        handler = MenuAddItemHandler(**mock_deps)
        
        handler.handle(
            name="Latte",
            price=Money(Decimal("1.0")),
            category=MenuItemCategory.COFFEE,
            ingredients_data={"Milk": 200.0},
            overwrite=True
        )
        
        mock_deps["menu_repo"].save.assert_called_once()

    def test_handle_ingredient_not_found(self, mock_deps):
        mock_deps["menu_repo"].get_by_name.return_value = None
        mock_deps["inventory_repo"].get_by_names.return_value = None
        
        handler = MenuAddItemHandler(**mock_deps)
        
        with pytest.raises(IngredientNotFoundError):
            handler.handle(
                name="Cappuccino",
                price=Money(Decimal("6.0")),
                category=MenuItemCategory.COFFEE,
                ingredients_data={"Secret Beans": 10.0},
                overwrite=False
            )

    def test_handle_multiple_ingredients(self, mock_deps):
        mock_deps["menu_repo"].get_by_name.return_value = None
        
        ing1 = MagicMock(spec=Ingredient)
        ing2 = MagicMock(spec=Ingredient)
        mock_deps["inventory_repo"].get_by_names.side_effect = [ing1, ing2]
        
        handler = MenuAddItemHandler(**mock_deps)
        
        ingredients_data = {"Beans": 15.0, "Water": 100.0}
        
        handler.handle(
            name="Americano",
            price=Money(Decimal("4.0")),
            category=MenuItemCategory.COFFEE,
            ingredients_data=ingredients_data,
            overwrite=False
        )
        
        saved_item = mock_deps["menu_repo"].save.call_args[0][0]
        assert len(saved_item.recipe.ingredients) == 2
        assert saved_item.recipe.ingredients[ing1] == 15.0
        assert saved_item.recipe.ingredients[ing2] == 100.0


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
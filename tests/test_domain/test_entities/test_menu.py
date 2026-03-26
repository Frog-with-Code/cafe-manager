import pytest

from cafe_manager.domain.entities.menu import (
    Unit,
    MenuItemType,
    MenuItemCategory,
    Ingredient,
    Recipe,
    MenuItem,
)
from cafe_manager.domain.entities.finance import Money


@pytest.fixture
def money():
    return Money.from_any(amount=100)


@pytest.fixture
def ingredient():
    return Ingredient(name="Water", unit=Unit.MILLILITER)


@pytest.fixture
def recipe():
    return Recipe(
        ingredients={Ingredient(name="Coffee Beans", unit=Unit.GRAM): 0.05},
    )


@pytest.fixture
def coffee_item(money, recipe):
    return MenuItem(
        name="Latte", recipe=recipe, price=money, category=MenuItemCategory.COFFEE
    )


@pytest.fixture
def tea_item(money, recipe):
    return MenuItem(
        name="Black Tea", recipe=recipe, price=money, category=MenuItemCategory.TEA
    )


class TestIngredient:
    def test_ingredient_creation(self):
        ing = Ingredient(name="Milk", unit=Unit.MILLILITER)
        assert ing.name == "Milk"
        assert ing.unit == Unit.MILLILITER


class TestRecipe:
    def test_recipe_creation(self):
        ingredients = {Ingredient("Sugar", Unit.GRAM): 10.0}
        recipe = Recipe(
            ingredients=ingredients,
        )
        assert Ingredient("Sugar", Unit.GRAM) in recipe.ingredients


class TestMenuItem:
    def test_menu_item_drink_type_inference(self, coffee_item):
        assert coffee_item.item_type == MenuItemType.DRINK

    def test_menu_item_category_coffee(self, coffee_item):
        assert coffee_item.category == MenuItemCategory.COFFEE
        assert coffee_item.requires_coffee_machine is True

    def test_menu_item_category_tea(self, tea_item):
        assert tea_item.item_type == MenuItemType.DRINK
        assert tea_item.category == MenuItemCategory.TEA
        assert tea_item.requires_coffee_machine is False


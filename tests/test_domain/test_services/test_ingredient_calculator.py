import pytest
from dataclasses import dataclass
from typing import ItemsView

from cafe_manager.domain.entities.menu import Ingredient, Unit, Recipe
from cafe_manager.domain.services.ingredient_calculator import IngredientCalculator


@dataclass(frozen=True)
class MenuItem:
    name: str
    recipe: Recipe


class TestIngredientCalculator:

    @pytest.fixture
    def calculator(self) -> IngredientCalculator:
        return IngredientCalculator()

    @pytest.fixture
    def dough(self) -> Ingredient:
        return Ingredient("Dough", Unit.GRAM)

    @pytest.fixture
    def cheese(self) -> Ingredient:
        return Ingredient("Cheese", Unit.GRAM)

    @pytest.fixture
    def tomato(self) -> Ingredient:
        return Ingredient("Tomato", Unit.GRAM)

    @pytest.fixture
    def pizza_item(self, dough, cheese, tomato) -> MenuItem:
        recipe = Recipe({dough: 2.0, cheese: 3.0, tomato: 1.0})
        return MenuItem("Pizza", recipe)

    @pytest.fixture
    def pasta_item(self, dough, cheese) -> MenuItem:
        recipe = Recipe({dough: 1.0, cheese: 2.0})
        return MenuItem("Pasta", recipe)

    def test_get_ingredients_required(
        self, calculator, pizza_item, dough, cheese, tomato
    ):
        items = calculator.get_ingredients_required(pizza_item.recipe)

        assert isinstance(items, ItemsView)
        assert len(items) == 3
        assert (dough, 2.0) in items

    def test_calculate_with_none(self, calculator):
        result = calculator.calculate(None)
        assert result == {}

    def test_calculate_with_empty_dict(self, calculator):
        result = calculator.calculate({})
        assert result == {}

    def test_calculate_single_item_multiplies_by_quantity(
        self, calculator, pizza_item, dough, cheese, tomato
    ):
        menu_items = {pizza_item: 2}

        result = calculator.calculate(menu_items)

        assert result[dough] == 4.0
        assert result[cheese] == 6.0
        assert result[tomato] == 2.0

    def test_calculate_multiple_items_aggregates_ingredients(
        self, calculator, pizza_item, pasta_item, dough, cheese, tomato
    ):
        menu_items = {pizza_item: 1, pasta_item: 3}

        result = calculator.calculate(menu_items)

        assert result[dough] == 5.0
        assert result[cheese] == 9.0
        assert result[tomato] == 1.0

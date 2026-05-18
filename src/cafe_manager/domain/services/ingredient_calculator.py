from typing import ItemsView

from cafe_manager.domain.services.interfaces import IngredientCalculator
from ..entities.menu import MenuItem, Ingredient, Recipe


class DefaultIngredientCalculator(IngredientCalculator):
    def get_ingredients_required(self, recipe: Recipe) -> ItemsView[Ingredient, float]:
        return recipe.ingredients.items()

    def calculate(self, menu_items: dict[MenuItem, int] | None) -> dict[Ingredient, float]:
        all_ingredients = {}

        if menu_items:
            for item, quantity in menu_items.items():
                for ingredient, amount in self.get_ingredients_required(item.recipe):
                    all_ingredients[ingredient] = (
                        all_ingredients.get(ingredient, 0) + (amount * quantity) 
                    )

        return all_ingredients

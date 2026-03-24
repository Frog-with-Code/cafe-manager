from dataclasses import dataclass
from enum import StrEnum

from .finance import Money


class Unit(StrEnum):
    MILLILITER = "ml"
    GRAM = "g"


class MenuItemType(StrEnum):
    DRINK = "drink"
    FOOD = "food"


class MenuItemCategory(StrEnum):
    COFFEE = "coffee"
    TEA = "tea"
    COCKTAIL = "cocktail"
    SMOOTHIE = "smoothie"
    BAKERY = "bakery"
    SOUP = "soup"


DRINKS_CATEGORIES: set[MenuItemCategory] = {
    MenuItemCategory.COFFEE,
    MenuItemCategory.TEA,
    MenuItemCategory.COCKTAIL,
    MenuItemCategory.SMOOTHIE,
}


@dataclass(frozen=True)
class Ingredient:
    name: str
    unit: Unit


@dataclass(frozen=True)
class Recipe:
    ingredients: dict[Ingredient, float]

    def __hash__(self) -> int:
        return hash((frozenset(self.ingredients.items())))


@dataclass(frozen=True)
class MenuItem:
    name: str
    recipe: Recipe
    price: Money
    category: MenuItemCategory

    @property
    def item_type(self) -> MenuItemType:
        return (
            MenuItemType.DRINK
            if self.category in DRINKS_CATEGORIES
            else MenuItemType.FOOD
        )

    @property
    def requires_coffee_machine(self) -> bool:
        return self.category == MenuItemCategory.COFFEE

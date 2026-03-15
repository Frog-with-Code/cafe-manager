from dataclasses import dataclass, field
from enum import StrEnum

from .finance import Money
from cafe_manager.common.exceptions import MenuItemTypeError


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
    requires_milk_foam: bool
    ingredients: dict[Ingredient, float]
    
    def __hash__(self) -> int:
        return hash((
            self.requires_milk_foam,
            frozenset(self.ingredients.items())
        ))


@dataclass(frozen=True)
class MenuItem:
    name: str
    recipe: Recipe
    price: Money
    category: MenuItemCategory
    item_type: MenuItemType = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, 
            'item_type', 
            MenuItemType.DRINK if self.category in DRINKS_CATEGORIES else MenuItemType.FOOD
    )

    @property
    def requires_coffee_machine(self) -> bool:
        return self.category == MenuItemCategory.COFFEE

    @property
    def requires_milk_foam(self) -> bool:
        return self.recipe.requires_milk_foam


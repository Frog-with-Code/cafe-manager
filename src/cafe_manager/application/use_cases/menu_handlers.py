from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import (
    Ingredient,
    MenuItemCategory,
    MenuItem,
    Recipe,
    MenuItemType,
)
from cafe_manager.application.interfaces import InventoryRepo, MenuRepo

from cafe_manager.common.exceptions import (
    IngredientNotFoundError,
    MenuItemExistsError,
    MenuItemNotFoundError,
)


class MenuInfoHandler:
    def __init__(self, menu_repo: MenuRepo) -> None:
        self._menu_repo = menu_repo

    def handle(self) -> dict[MenuItemType, list[MenuItem]]:
        menu_items = self._menu_repo.get_all()

        if not menu_items:
            return {}

        grouped_menu = {}
        for item in menu_items:
            item_type = item.item_type

            if item_type not in grouped_menu:
                grouped_menu[item_type] = []

            grouped_menu[item_type].append(item)

        return grouped_menu


class MenuAddItemHandler:
    def __init__(self, menu_repo: MenuRepo, inventory_repo: InventoryRepo) -> None:
        self._menu_repo = menu_repo
        self._inventory_repo = inventory_repo

    def handle(
        self,
        name: str,
        price: Money,
        category: MenuItemCategory,
        ingredients_data: dict[str, float],
        overwrite: bool,
    ) -> None:
        if not overwrite and self._menu_repo.get_by_name(name):
            raise MenuItemExistsError(f"Menu item with name '{name}' already exists")

        ingredients = {}
        for ingr_name, amount in ingredients_data.items():
            ingr_dict = self._inventory_repo.get_by_names({ingr_name})

            if ingr_dict is None:
                raise IngredientNotFoundError(f"Ingredient '{ingr_name}' is unknown")

            ingr = next(iter(ingr_dict))
            ingredients[ingr] = amount

        recipe = Recipe(ingredients=ingredients)
        item = MenuItem(name=name, recipe=recipe, price=price, category=category)

        self._menu_repo.save(item)


class MenuItemRemoveHandler:
    def __init__(self, menu_repo: MenuRepo) -> None:
        self._menu_repo = menu_repo

    def handle(self, name: str) -> None:
        if self._menu_repo.get_by_name(name) is None:
            raise MenuItemNotFoundError(
                f"Impossible to remove item with name '{name}', because it doesn't exist"
            )

        self._menu_repo.delete_by_name(name)


class MenuListIngredientsHandler:
    def __init__(self, menu_repo: MenuRepo) -> None:
        self._menu_repo = menu_repo

    def handle(self, name: str) -> dict[Ingredient, float]:
        menu_item = self._menu_repo.get_by_name(name)

        if menu_item is None:
            raise MenuItemNotFoundError(f"Menu item with name '{name}' was not found")

        return menu_item.recipe.ingredients

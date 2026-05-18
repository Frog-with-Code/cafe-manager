from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import (
    Ingredient,
    MenuItemCategory,
    MenuItem,
    Recipe,
    MenuItemType,
)
from cafe_manager.application.uow import UnitOfWork

from cafe_manager.common.exceptions import (
    IngredientNotFoundError,
    MenuItemExistsError,
    MenuItemNotFoundError,
)


class MenuInfoHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self) -> dict[MenuItemType, list[MenuItem]]:
        with self._uow as uow:
            menu_items = uow.menu_repo.get_all()

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
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(
        self,
        name: str,
        price: Money,
        category: MenuItemCategory,
        ingredients_data: dict[str, float],
        overwrite: bool,
    ) -> None:
        with self._uow as uow:
            if not overwrite and uow.menu_repo.get_by_name(name):
                raise MenuItemExistsError(
                    f"Menu item with name '{name}' already exists"
                )

            ingredients = {}
            for ingr_name, amount in ingredients_data.items():
                ingr_dict = uow.inventory_repo.get_by_names({ingr_name})

                if ingr_dict is None:
                    raise IngredientNotFoundError(
                        f"Ingredient '{ingr_name}' is unknown"
                    )

                ingr = next(iter(ingr_dict))
                ingredients[ingr] = amount

            recipe = Recipe(ingredients=ingredients)
            item = MenuItem(
                name=name, recipe=recipe, price=price, category=category
            )

            uow.menu_repo.save(item)


class MenuItemRemoveHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, name: str) -> None:
        with self._uow as uow:
            if uow.menu_repo.get_by_name(name) is None:
                raise MenuItemNotFoundError(
                    f"Impossible to remove item with name '{name}', because it doesn't exist"
                )

            uow.menu_repo.delete_by_name(name)


class MenuListIngredientsHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, name: str) -> dict[Ingredient, float]:
        with self._uow as uow:
            menu_item = uow.menu_repo.get_by_name(name)

            if menu_item is None:
                raise MenuItemNotFoundError(
                    f"Menu item with name '{name}' was not found"
                )

            return menu_item.recipe.ingredients

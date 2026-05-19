from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from ..schemas import IngredientInfo, MenuItemResponse
from ..dependencies import get_uow

from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import MenuItemCategory

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.menu_handlers import (
    MenuAddItemHandler,
    MenuInfoHandler,
    MenuItemRemoveHandler,
    MenuListIngredientsHandler,
)

router = APIRouter()


@router.get("/", response_model=dict[str, list[MenuItemResponse]])
def get_menu_info(uow: UnitOfWork = Depends(get_uow)):
    """Show all menu items grouped by type (DRINK/FOOD)"""
    handler = MenuInfoHandler(uow)
    grouped_items = handler.handle()

    return {
        str(item_type): [
            {"name": item.name, "price": str(item.price), "category": item.category}
            for item in items
        ]
        for item_type, items in grouped_items.items()
    }


@router.post("/", status_code=201)
def add_menu_item(
    name: Annotated[str, Query(min_length=2)],
    price: Annotated[float, Query(ge=0)],
    category: MenuItemCategory,
    ingredients: dict[str, float],
    overwrite: bool = False,
    uow: UnitOfWork = Depends(get_uow),
):
    """Add a new item to the menu with its recipe"""
    if not ingredients:
        raise HTTPException(
            status_code=400, detail="Impossible to add menu item without ingredients"
        )

    handler = MenuAddItemHandler(uow)
    handler.handle(
        name=name,
        price=Money.from_any(price),
        category=category,
        ingredients_data=ingredients,
        overwrite=overwrite,
    )
    return {"status": "success", "message": f"Item '{name}' added to menu"}


@router.delete("/{name}", status_code=200)
def remove_menu_item(
    name: Annotated[str, Path(min_length=2)], uow: UnitOfWork = Depends(get_uow)
):
    """Remove an item from the menu"""
    handler = MenuItemRemoveHandler(uow)
    handler.handle(name)
    return {"status": "success", "message": f"Item '{name}' removed"}


@router.get("/{name}/ingredients", response_model=list[IngredientInfo])
def get_item_ingredients(
    name: Annotated[str, Path(min_length=2)], uow: UnitOfWork = Depends(get_uow)
):
    """List all ingredients and their amounts for a specific menu item"""
    handler = MenuListIngredientsHandler(uow)
    ingredients = handler.handle(name)
    return [
        {"name": ingr.name, "amount": amount, "unit": ingr.unit}
        for ingr, amount in ingredients.items()
    ]

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Path

from ..dependencies import get_uow
from ..shemas import InventoryResponse

from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import Unit

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.inventory_handlers import (
    InventoryAddHandler,
    InventoryInfoHandler,
    InventoryRemoveHandler,
    InventorySupplyHandler,
)

router = APIRouter()


@router.post("/", status_code=201)
def add_ingredient(
    name: Annotated[str, Query(min_length=2)],
    unit: Unit,
    overwrite: Annotated[
        bool, Query(description="Overwrite info if ingredient with such name exists")
    ] = False,
    uow: UnitOfWork = Depends(get_uow),
):
    """Add new ingredient to the inventory"""
    handler = InventoryAddHandler(uow)
    handler.handle(name, unit, overwrite)
    return {"status": "success", "message": f"Ingredient '{name}' added"}


@router.delete("/{name}", status_code=200)
def remove_ingredient(
    name: Annotated[str, Path(min_length=2)], uow: UnitOfWork = Depends(get_uow)
):
    """Remove ingredient with all its stocks from the inventory"""
    handler = InventoryRemoveHandler(uow)
    handler.handle(name)
    return {"status": "success", "message": f"Ingredient '{name}' removed"}


@router.get("/", response_model=list[InventoryResponse])
def get_inventory_info(uow: UnitOfWork = Depends(get_uow)):
    """Show info about inventory items"""
    handler = InventoryInfoHandler(uow)
    ingredients = handler.handle()

    return [
        {"name": ingr.name, "unit": ingr.unit, "amount": amount}
        for ingr, amount in ingredients.items()
    ]


@router.post("/supply", status_code=200)
def supply_inventory(
    name: Annotated[str, Query(min_length=2)],
    quantity: Annotated[float, Query(gt=0)],
    price: Annotated[float, Query(ge=0)],
    account_id: UUID | None = None,
    uow: UnitOfWork = Depends(get_uow),
):
    """Supply inventory with existing ingredient"""
    handler = InventorySupplyHandler(uow)
    handler.handle(
        name=name,
        amount=quantity,
        price=Money.from_any(price),
        account_id=account_id,
    )
    return {
        "status": "success",
        "message": f"Inventory supplied by '{name}' in amount of {quantity}",
    }

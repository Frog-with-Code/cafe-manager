from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_uow
from ..schemas import OrderResponse

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.kitchen_handlers import (
    KitchenListPending,
    KitchenReadyHandler,
    KitchenStartHandler,
)

from cafe_manager.infrastructure.factory import get_ingredient_calculator

router = APIRouter()


@router.get("/pending", response_model=list[OrderResponse])
def list_pending_orders(uow: UnitOfWork = Depends(get_uow)):
    """Get a list of all paid orders waiting to be cooked"""
    handler = KitchenListPending(uow)
    orders = handler.handle()
    return orders


@router.post("/start")
def start_cooking(employee_id: str | None = None, uow: UnitOfWork = Depends(get_uow)):
    """Assign an employee and start cooking the oldest pending order"""
    ingredient_calculator = get_ingredient_calculator()
    handler = KitchenStartHandler(
        uow=uow,
        ingredient_calculator=ingredient_calculator,
    )

    order_id, emp_id, machine_id = handler.handle(employee_id)
    if order_id is None:
        return {"status": "success", "message": "No pending orders"}

    return {
        "status": "success",
        "order_id": order_id,
        "employee_id": emp_id,
        "machine_id": machine_id,
    }


@router.post("/{order_id}/complete")
def complete_order(order_id: str, uow: UnitOfWork = Depends(get_uow)):
    """Mark an order as ready for serving"""
    handler = KitchenReadyHandler(uow)

    handler.handle(order_id)
    return {"status": "success", "message": "Order was completed"}

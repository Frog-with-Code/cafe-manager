from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_uow
from ..shemas import OrderResponse

from cafe_manager.domain.entities.finance import Money

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.order_handlers import (
    OrderCreateHandler,
    OrderInfoHandler,
    OrderPayHandler,
    OrderServeHandler,
    OrderShowItemsHandler,
)

from cafe_manager.infrastructure.factory import (
    get_id_generator,
    get_ingredient_calculator,
    get_payment_service,
)

router = APIRouter()


@router.post("/", status_code=201)
def create_order(
    items: dict[str, int],
    table_id: int | None = None,
    continue_session: Annotated[
        bool, Query(description="Add order to the already occupied table")
    ] = False,
    uow: UnitOfWork = Depends(get_uow),
):
    """
    Create a new order.
    Items should be a dictionary of {menu_item_name: amount}.
    """
    ordered_items = list(items.items())

    ingredient_calculator = get_ingredient_calculator()
    id_generator = get_id_generator()
    handler = OrderCreateHandler(
        uow=uow,
        ingredient_calculator=ingredient_calculator,
        id_generator=id_generator,
    )

    order_id = handler.handle(ordered_items, table_id, continue_session)
    return {
        "status": "success",
        "order_id": order_id,
        "message": f"Order with ID '{order_id}' was created'",
    }


@router.post("/{order_id}/pay", status_code=200)
def pay_order(
    order_id: str,
    amount_provided: float,
    account_id: UUID | None = None,
    client_id: str | None = None,
    uow: UnitOfWork = Depends(get_uow),
):
    """Process payment for an existing order"""
    payment_service = get_payment_service()
    handler = OrderPayHandler(uow=uow, payment_service=payment_service)

    handler.handle(
        order_id=order_id,
        cash_provided=Money.from_any(amount_provided),
        account_id=account_id,
        client_id=client_id,
    )
    return {"status": "success", "message": "Order with ID 'order_id' was paid"}


@router.get("/active", response_model=list[OrderResponse])
def get_active_orders(uow: UnitOfWork = Depends(get_uow)):
    """List all orders that are not completed yet"""
    handler = OrderInfoHandler(uow)
    return handler.handle()


@router.post("/{order_id}/serve", status_code=200)
def serve_order(
    order_id: str,
    uow: UnitOfWork = Depends(get_uow),
):
    """Mark an order as served and free the employee"""
    handler = OrderServeHandler(uow)
    handler.handle(order_id)
    return {"status": "success", "message": f"Order with ID '{order_id}' was served"}


@router.get("/{order_id}/items")
def get_order_items(order_id: str, uow: UnitOfWork = Depends(get_uow)):
    handler = OrderShowItemsHandler(uow)
    items = handler.handle(order_id)
    return {
        "status": "success",
        "items": {ingr.name: qty for ingr, qty in items.items()},
    }

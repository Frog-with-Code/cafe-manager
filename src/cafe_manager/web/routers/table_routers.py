from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_uow
from ..schemas import TableResponse

from cafe_manager.domain.entities.finance import Money

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.table_handlers import (
    AssignChairToTableHandler,
    TableBuyHandler,
    TableDiscardHandler,
    TableFreeHandler,
    TableInfoHandler,
    TableReserveHandler,
)

from cafe_manager.infrastructure.factory import get_seating_service

router = APIRouter()


@router.post("/", status_code=201)
def buy_table(
    price: Annotated[float, Query(ge=0)],
    seats: int = 4,
    account_id: UUID | None = None,
    uow: UnitOfWork = Depends(get_uow),
):
    """Buy a new table with a specific seating capacity"""
    handler = TableBuyHandler(uow)
    handler.handle(price=Money.from_any(price), seats=seats, account_id=account_id)
    return {"status": "success", "message": f"New {seats}-seats table was bought"}


@router.delete("/{table_id}", status_code=200)
def discard_table(table_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Discard a table by its ID"""
    handler = TableDiscardHandler(uow)
    handler.handle(table_id)
    return {"status": "success", "message": f"Table with ID '{table_id}' discarded"}


@router.get("/", response_model=list[TableResponse])
def get_tables_info(uow: UnitOfWork = Depends(get_uow)):
    """Show information about all tables"""
    handler = TableInfoHandler(uow)
    return handler.handle()


@router.post("/reserve", status_code=200)
def reserve_table(
    seats_required: Annotated[int, Query(gt=0)], uow: UnitOfWork = Depends(get_uow)
):
    """Find and reserve a suitable table for the given number of people"""
    seating_service = get_seating_service()
    handler = TableReserveHandler(uow, seating_service)
    table_id = handler.handle(seats_required)
    return {"status": "success", "table_id": table_id}


@router.post("/{table_id}/free", status_code=200)
def free_table(table_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Free a reserved or occupied table"""
    handler = TableFreeHandler(uow)
    handler.handle(table_id)
    return {"status": "success", "message": f"Table with ID '{table_id}' was freed"}


@router.post("/{table_id}/assign-chair/{chair_id}", status_code=200)
def assign_chair_to_table(
    table_id: int, chair_id: int, uow: UnitOfWork = Depends(get_uow)
):
    """Move a specific chair to a specific table"""
    handler = AssignChairToTableHandler(uow)
    handler.handle(table_id=table_id, chair_id=chair_id)
    return {
        "status": "success",
        "message": f"Chair {chair_id} assigned to table {table_id}",
    }

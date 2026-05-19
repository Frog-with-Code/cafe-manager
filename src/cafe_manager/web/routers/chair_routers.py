from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Query

from ..schemas import ChairResponse
from ..dependencies import get_uow

from cafe_manager.domain.entities.equipment import Chair
from cafe_manager.domain.entities.finance import Money

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.chair_handlers import (
    ChairBuyHandler,
    ChairDiscardHandler,
    ChairInfoHandler,
)

router = APIRouter()


@router.post("/buy", status_code=201)
def buy(
    price: Annotated[float, Query(ge=0)],
    account_id: UUID | None = None,
    uow: UnitOfWork = Depends(get_uow),
):
    """Buy new chair"""
    handler = ChairBuyHandler(uow)
    conv_price = Money.from_any(price)
    handler.handle(conv_price, account_id)
    return {"status": "success", "message": "Chair bought"}


@router.delete("/discard", status_code=200)
def discard(chair_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Discard chair by its ID"""
    handler = ChairDiscardHandler(uow)
    handler.handle(chair_id)
    return {"status": "success", "message": f"Chair with ID '{chair_id}' was discarded"}


@router.get("/info", response_model=list[ChairResponse])
def info(
    uow: UnitOfWork = Depends(get_uow),
) -> list[Chair]:
    """Show info about chairs"""
    handler = ChairInfoHandler(uow)
    return handler.handle()

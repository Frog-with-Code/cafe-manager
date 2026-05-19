from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ..schemas import FinanceStatsResponse, TransactionResponse
from ..dependencies import get_uow

from cafe_manager.domain.entities.finance import Money

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.finance_handlers import (
    FinanceHistoryHandler,
    FinanceInvestHandler,
    FinanceSetPrimaryHandler,
    FinanceStatsHandler,
)

router = APIRouter()


@router.post("/invest", status_code=200)
def invest(
    amount: Annotated[float, Query(ge=0)],
    description: str = "Investment",
    account_id: UUID | None = None,
    uow: UnitOfWork = Depends(get_uow),
):
    """Invest money into a cafe account"""
    handler = FinanceInvestHandler(uow)
    handler.handle(Money.from_any(amount), account_id, description)
    return {"status": "success", "message": "Money invested"}


@router.get("/stats", response_model=FinanceStatsResponse)
def get_stats(
    account_id: UUID | None = None,
    start: (
        Annotated[
            datetime, Query(description="Start date of the time span for the stats")
        ]
        | None
    ) = None,
    end: (
        Annotated[
            datetime, Query(description="End date of the time span for the stats")
        ]
        | None
    ) = None,
    uow: UnitOfWork = Depends(get_uow),
):
    """Get financial statistics for a period"""
    handler = FinanceStatsHandler(uow)
    stats = handler.handle(account_id, start, end)

    return {
        "id": stats["id"],
        "balance": str(stats["balance"]),
        "income": str(stats["income"]),
        "expense": str(stats["expense"]),
        "profit_abs": str(stats["profit_abs"]),
        "is_loss": stats["is_loss"],
    }


@router.get("/history", response_model=list[TransactionResponse])
def get_history(
    account_id: UUID | None = None,
    limit: Annotated[int, Query(gt=0)] = 5,
    uow: UnitOfWork = Depends(get_uow),
):
    """Show the latest financial transactions"""
    handler = FinanceHistoryHandler(uow)
    history = handler.handle(account_id, limit)
    if not history:
        return []

    return [
        {
            "transaction_id": t.transaction_id,
            "transaction_type": t.transaction_type,
            "money": str(t.money),
            "description": t.description,
            "time": t.time,
        }
        for t in history
    ]


@router.post("/primary/{account_id}", status_code=200)
def set_primary(account_id: UUID, uow: UnitOfWork = Depends(get_uow)):
    """Set account as primary for operations without explicit ID"""
    handler = FinanceSetPrimaryHandler(uow)
    handler.handle(account_id)
    return {"status": "success", "message": "Account set as primary"}

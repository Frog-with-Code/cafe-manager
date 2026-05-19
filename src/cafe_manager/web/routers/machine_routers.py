from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from ..dependencies import get_uow
from ..schemas import CoffeeMachineResponse

from cafe_manager.domain.entities.finance import Money

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.machine_handlers import (
    CoffeeMachineBuyHandler,
    CoffeeMachineDiscardHandler,
    CoffeeMachineInfoHandler,
    CoffeeMachineResumeHandler,
    CoffeeMachineServiceHandler,
)

router = APIRouter()


@router.post("/", status_code=201)
def buy_machine(
    price: Annotated[float, Query(ge=0)],
    model: str,
    limit: Annotated[
        int,
        Query(gt=0, description="Limit of working cycles before maintenance required"),
    ] = 1000,
    account_id: UUID | None = None,
    uow: UnitOfWork = Depends(get_uow),
):
    """Buy a new coffee machine"""
    handler = CoffeeMachineBuyHandler(uow)
    handler.handle(
        price=Money.from_any(price), model=model, limit=limit, account_id=account_id
    )
    return {
        "status": "success",
        "message": f"Coffee-machine of model '{model}' bought",
    }


@router.delete("/{machine_id}", status_code=200)
def discard_machine(machine_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Discard a coffee machine by its ID"""
    handler = CoffeeMachineDiscardHandler(uow)
    handler.handle(machine_id)
    return {
        "status": "success",
        "message": f"Coffee-machine with ID '{machine_id}' discarded",
    }


@router.get("/", response_model=list[CoffeeMachineResponse])
def get_machines_info(uow: UnitOfWork = Depends(get_uow)):
    """Show information about all coffee machines"""
    handler = CoffeeMachineInfoHandler(uow)
    return handler.handle()


@router.post("/{machine_id}/service", status_code=200)
def service_machine(machine_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Send coffee machine for technical maintenance"""
    handler = CoffeeMachineServiceHandler(uow)
    handler.handle(machine_id)
    return {
        "status": "success",
        "message": f"Coffee-machine with ID '{machine_id}' sent to service",
    }


@router.post("/{machine_id}/resume", status_code=200)
def resume_machine(machine_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Resume coffee machine work after maintenance"""
    handler = CoffeeMachineResumeHandler(uow)
    handler.handle(machine_id)
    return {
        "status": "success",
        "message": f"Coffee-machine with ID '{machine_id}' resumed work",
    }

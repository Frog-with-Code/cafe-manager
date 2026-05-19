from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_uow
from ..schemas import ClientResponse

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.client_handlers import (
    ClientCreateHandler,
    ClientInfoHandler,
    ClientListHandler,
)

from cafe_manager.infrastructure.factory import get_id_generator

router = APIRouter()


@router.post("/", status_code=201)
def create_client(
    name: Annotated[str, Query(min_length=2)], uow: UnitOfWork = Depends(get_uow)
):
    id_generator = get_id_generator()
    handler = ClientCreateHandler(uow, id_generator)
    client_id = handler.handle(name)
    return {
        "status": "success",
        "id": client_id,
        "message": f"Client with ID '{client_id}' was registered",
    }


@router.get("/{client_id}", response_model=ClientResponse)
def get_client_info(client_id: str, uow: UnitOfWork = Depends(get_uow)):
    handler = ClientInfoHandler(uow)
    return handler.handle(client_id)


@router.get("/", response_model=list[ClientResponse])
def list_clients(
    uow: UnitOfWork = Depends(get_uow),
):
    handler = ClientListHandler(uow)
    return handler.handle()

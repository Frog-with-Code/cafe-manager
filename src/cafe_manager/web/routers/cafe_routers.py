from typing import Annotated

from fastapi import APIRouter, Depends, Query, status, Path

from ..dependencies import get_uow
from ..shemas import CafeEnvResponse

from cafe_manager.conf import CAFES_STORAGE_DIR

from cafe_manager.domain.entities.finance import Money
from cafe_manager.application.uow import UnitOfWork
from cafe_manager.application.use_cases.cafe_handlers import (
    CafeCreateHandler,
    CafeRemoveHandler,
    CafeActivateHandler,
    CafeDeactivateHandler,
    CafeInitHandler,
)
from cafe_manager.infrastructure.env_manager import EnvironmentManager

router = APIRouter()
env_manager = EnvironmentManager()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_cafe(name: Annotated[str, Query(min_length=2)]):
    """Create a new cafe database environment"""
    handler = CafeCreateHandler(CAFES_STORAGE_DIR, env_manager)
    handler.handle(name)
    return {"status": "success", "message": f"Cafe environment '{name}' created"}


@router.delete("/{name}")
def remove_cafe(name: Annotated[str, Path(min_length=2)]):
    """Irrevocably remove a cafe environment"""
    handler = CafeRemoveHandler(env_manager)
    handler.handle(name)
    return {"status": "success", "message": f"Cafe environment '{name}' deleted"}


@router.post("/activate/{name}")
def activate_cafe(name: Annotated[str, Path(min_length=2)]):
    """Activate a specific cafe environment"""
    handler = CafeActivateHandler(CAFES_STORAGE_DIR, env_manager)
    handler.handle(name)
    return {"status": "success", "message": f"Cafe environment '{name}' activated"}


@router.post("/deactivate")
def deactivate_cafe():
    """Deactivate the current cafe environment"""
    handler = CafeDeactivateHandler(env_manager)
    try:
        handler.handle()
    except FileNotFoundError:
        pass
    return {"status": "success", "message": "Cafe environment deactivated"}


@router.post("/init")
def init_cafe(
    name: Annotated[str, Query(min_length=2)],
    address: Annotated[str, Query(min_length=5)],
    capital: Annotated[float, Query(ge=0)] = 0.0,
    uow: UnitOfWork = Depends(get_uow),
):
    """Initialize metadata for the currently active environment"""
    handler = CafeInitHandler(uow)
    handler.handle(name, address, Money.from_any(capital))
    return {"status": "success", "message": "Environment initialized"}


@router.get("/", response_model=list[CafeEnvResponse])
def list_cafes():
    """List all available cafe environments"""
    active_env = env_manager.get_active_env_path()
    envs = []

    for env_file in CAFES_STORAGE_DIR.glob("*.db"):
        is_active = False
        if active_env and env_file.resolve() == active_env.resolve():
            is_active = True

        envs.append(
            CafeEnvResponse(
                name=env_file.stem, path=str(env_file.resolve()), is_active=is_active
            )
        )
    return envs

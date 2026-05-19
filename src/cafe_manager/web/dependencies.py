from fastapi import HTTPException

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.infrastructure.factory import create_uow, get_active_path

def get_uow() -> UnitOfWork:
    try:
        db_path = get_active_path()
        return create_uow(db_path)
    except RuntimeError:
        raise HTTPException(
            status_code=400, 
            detail="No active cafe environment"
        )
from pathlib import Path
import typer

from cafe_manager.application.uow import UnitOfWork
from cafe_manager.infrastructure.factory import create_uow, get_active_path
from cafe_manager.common.exceptions import CLIBusinessError

def init_context(ctx: typer.Context) -> None:
    try:
        active_env_path = get_active_path()
        uow = create_uow(active_env_path)
        
        ctx.obj = {
            "active_env": active_env_path,
            "uow": uow
        }
    except FileNotFoundError:
        raise CLIBusinessError(
            "Impossible to execute command. No active cafe environment. "
            "Use 'cafe activate <name>' first."
        )
    except Exception as e:
        raise CLIBusinessError(f"Failed to initialize database: {str(e)}")


def get_env_path(ctx: typer.Context) -> Path:
    return ctx.obj["active_env"]


def get_uow(ctx: typer.Context) -> UnitOfWork:
    return ctx.obj["uow"]
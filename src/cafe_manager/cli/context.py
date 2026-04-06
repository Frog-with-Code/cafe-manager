from pathlib import Path
import typer

from cafe_manager.application.interfaces import UnitOfWork

from cafe_manager.infrastructure.env_manager import EnvironmentManager
from cafe_manager.infrastructure.sqlite.uow import SQLiteUnitOfWork

from cafe_manager.common.exceptions import CLIBusinessError

BASE_DIR = Path(__file__).parent.parent.parent.parent / "cafes"


def init_context(ctx: typer.Context) -> None:
    env_manager = EnvironmentManager()

    active_env = env_manager.get_active_env_path(BASE_DIR)
    if active_env is None:
        raise CLIBusinessError(
            "Impossible to execute command. No active cafe environment"
        )

    ctx.obj = {"active_env": active_env, "uow": SQLiteUnitOfWork(active_env)}


def get_env_path(ctx: typer.Context) -> Path:
    return ctx.obj["active_env"]


def get_uow(ctx: typer.Context) -> UnitOfWork:
    return ctx.obj["uow"]

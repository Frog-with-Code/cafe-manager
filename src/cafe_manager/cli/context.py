import typer
from pathlib import Path

from cafe_manager.common.exceptions import CLIBusinessError
from cafe_manager.infrastructure.sqlite.env_manager import EnvironmentManager

BASE_DIR = Path(__file__).parent.parent.parent.parent / "cafes"

def init_context(ctx: typer.Context) -> None:
    env_manager = EnvironmentManager()
    
    active_env = env_manager.get_active_env_path(BASE_DIR)
    if active_env is None:
        raise CLIBusinessError("Impossible to execute command. No active cafe environment")
    
    ctx.obj = {"active_env": active_env}
        
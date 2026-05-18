from typing import Annotated

import typer

from ..styles import print_info, print_info_important, print_success
from ..custom_types import Money, parse_money
from ..context import get_uow, init_context

from cafe_manager.conf import CAFES_STORAGE_DIR

from cafe_manager.application.use_cases.cafe_handlers import (
    CafeCreateHandler,
    CafeRemoveHandler,
    CafeActivateHandler,
    CafeDeactivateHandler,
    CafeInitHandler,
    CafeEnvExistsError,
    CafeEnvNotFoundError,
    CafeEnvNoActiveError,
    CafeEnvAlreadyInitError,
)

from cafe_manager.infrastructure.env_manager import EnvironmentManager

from cafe_manager.common.exceptions import (
    CLIUnexpectedError,
    CLIBusinessError,
    CafeEnvNameError,
)

app = typer.Typer(help="Manage cafe databases and working environments")
env_manager = EnvironmentManager()


@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Name of the new cafe environment")],
):
    """Create new cafe environment"""
    try:
        handler = CafeCreateHandler(CAFES_STORAGE_DIR, env_manager)
        handler.handle(name)

        print_success(f"New cafe environment with name '{name}' was created")
    except (CafeEnvExistsError, CafeEnvNameError) as e:
        raise CLIBusinessError(str(e))
    except Exception as e:
        raise CLIUnexpectedError(str(e))


@app.command()
def remove(
    name: Annotated[
        str,
        typer.Argument(
            help="Name of the cafe",
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            prompt="Warning! This operation is not reversible. Are you sure you want to delete this cafe?",
            help="Don't ask your permission before performing",
        ),
    ] = False,
):
    """Irrevocably remove cafe environment"""
    try:
        if force:
            handler = CafeRemoveHandler(env_manager)
            handler.handle(name)

            print_success(f"Cafe environment with name '{name}' was deleted")
    except CafeEnvNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def activate(
    name: Annotated[str, typer.Argument(help="Name of the cafe environment")],
):
    """Activate cafe environment"""
    try:
        handler = CafeActivateHandler(CAFES_STORAGE_DIR, env_manager)
        handler.handle(name)

        print_success(f"Cafe environment with name '{name}' was activated")
    except CafeEnvNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def deactivate():
    """Deactivate cafe environment"""
    try:
        handler = CafeDeactivateHandler(env_manager)
        handler.handle()

        print_success("Cafe environment was deactivated")
    except CafeEnvNoActiveError:
        pass


@app.command()
def init(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the cafe")],
    address: Annotated[
        str, typer.Option("--address", "-a", help="Address of the cafe")
    ],
    capital: Annotated[
        Money,
        typer.Option(
            "--capital", "-c", parser=parse_money, help="Starting capital of the cafe"
        ),
    ] = Money(),
):
    """Initialize cafe's metadata"""
    init_context(ctx)
    uow = get_uow(ctx)
    handler = CafeInitHandler(uow)
    try:
        handler.handle(name, address, capital)

        print_success("Environment was initialized")
    except CafeEnvAlreadyInitError as e:
        raise CLIBusinessError(str(e))


@app.command(name="list")
def env_list():
    """Show list of existing cafes"""
    active_env = env_manager.get_active_env_path()

    for env in CAFES_STORAGE_DIR.glob("*.db"):
        message = f"{env.stem:<30} {env.resolve()}"
        if active_env and env.resolve() == active_env.resolve():
            print_info_important(message)
        else:
            print_info(message)

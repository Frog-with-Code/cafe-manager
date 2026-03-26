import typer
from typing import Annotated
from rich.console import Console

from cafe_manager.common.exceptions import (
    CLIUnexpectedError,
    CLIBusinessError,
    CafeEnvNameError,
)
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)

from .custom_types import Money, parse_money
from .context import get_env_path, init_context, BASE_DIR
from cafe_manager.infrastructure.sqlite.env_manager import EnvironmentManager
from cafe_manager.application.use_cases.cafe_handlers import *
from cafe_manager.infrastructure.sqlite.repositories.cafe_repo import SQLiteCafeRepo

app = typer.Typer()
console = Console()
env_manager = EnvironmentManager()


@app.command()
def create(
    name: Annotated[
        str, typer.Option("--name", "-n", help="Name of the new cafe environment")
    ],
):
    """Create new cafe environment"""

    try:
        handler = CafeCreateHandler(BASE_DIR, env_manager)
        handler.handle(name)
        console.print(
            f"[bold blue]New cafe environment with name {name} was created[/bold blue]"
        )
    except (CafeEnvExistsError, CafeEnvNameError) as e:
        raise CLIBusinessError(str(e))
    except Exception as e:
        raise CLIUnexpectedError(str(e))


@app.command()
def remove(
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
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
    """Remove cafe environment"""
    try:
        if force:
            handler = CafeRemoveHandler(BASE_DIR, env_manager, BASE_DIR)
            handler.handle(name)
            console.print(
                f"[bold blue]Cafe environment with name {name} was deleted[/bold blue]"
            )
    except CafeEnvNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def activate(
    name: Annotated[
        str, typer.Option("--name", "-n", help="Name of the cafe environment")
    ],
):
    """Activate cafe environment"""
    try:
        handler = CafeActivateHandler(BASE_DIR, env_manager, BASE_DIR)
        handler.handle(name)
        console.print(
            f"[bold blue]Cafe environment with name {name} was activated[/bold blue]"
        )
    except CafeEnvNoActiveError as e:
        raise CLIBusinessError(str(e))


@app.command()
def deactivate():
    """Deactivate cafe environment"""
    try:
        handler = CafeDeactivateHandler(BASE_DIR, env_manager, BASE_DIR)
        handler.handle()
        console.print(f"[bold blue]Cafe environment was deactivated[/bold blue]")
    except CafeEnvNoActiveError as e:
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
    """Initialize new cafe environment. Set metadata of the cafe and create its financial account"""
    init_context(ctx)
    env_path = get_env_path(ctx)

    cafe_repo = SQLiteCafeRepo(env_path)
    finance_repo = SQLiteFinanceRepo(env_path)
    handler = CafeInitHandler(cafe_repo, finance_repo)
    try:
        handler.handle(name, address, capital)

        console.print("[bold blue]Environment was initialized[/bold blue]")
    except CafeEnvAlreadyInitError as e:
        raise CLIBusinessError(str(e))


@app.command(name="list")
def env_list(ctx: typer.Context) -> None:
    """Show list of cafe environments"""
    init_context(ctx)
    active_env = get_env_path(ctx)

    for env in BASE_DIR.glob("*.db"):
        l_border, r_border = (
            ("[bold blue]", "[/bold blue]")
            if env == active_env
            else ("[dim blue]", "[/dim blue]")
        )
        console.print(f"{l_border}{env.stem:<30} {env.resolve()}{r_border}")

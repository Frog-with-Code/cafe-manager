import typer
from typing import Annotated

from cafe_manager.common.exceptions import (
    CLIUnexpectedError,
    CLIBusinessError,
    CafeEnvNameError,
    RecordNotUpdatedError,
)
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)

from .custom_types import Money, parse_money
from .context import init_context, BASE_DIR
from cafe_manager.infrastructure.sqlite.env_manager import EnvironmentManager
from cafe_manager.applications.use_cases.cafe_handlers import *
from cafe_manager.infrastructure.sqlite.repositories.cafe_repo import SQLiteCafeRepo

app = typer.Typer()

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
        print(f"New cafe environment with name {name} was created")
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
        ),
    ] = False,
):
    """Remove cafe environment"""
    try:
        if force:
            handler = CafeRemoveHandler(BASE_DIR, env_manager, BASE_DIR)
            handler.handle(name)
            print(f"Cafe environment with name {name} was deleted")
    except CafeEnvNotFoundError as e:
        raise CLIBusinessError(str(e))
    except Exception as e:
        raise CLIUnexpectedError(str(e))


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
        print(f"Cafe environment with name {name} was activated")
    except CafeEnvNoActiveError as e:
        raise CLIBusinessError(str(e))
    except Exception as e:
        raise CLIUnexpectedError(str(e))


@app.command()
def deactivate():
    """Deactivate cafe environment"""
    try:
        handler = CafeDeactivateHandler(BASE_DIR, env_manager, BASE_DIR)
        handler.handle()
        print(f"Cafe environment was deactivated")
    except CafeEnvNoActiveError as e:
        pass
    except Exception as e:
        raise CLIUnexpectedError(str(e))


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

    try:
        env = ctx.obj["active_env"]
        cafe_repo = SQLiteCafeRepo(env)
        finance_repo = SQLiteFinanceRepo(env)

        handler = CafeInitHandler(cafe_repo, finance_repo)
        handler.handle(name, address, capital)
    except CafeEnvAlreadyInitError as e:
        raise CLIBusinessError(str(e))
    except Exception as e:
        raise CLIUnexpectedError(str(e))

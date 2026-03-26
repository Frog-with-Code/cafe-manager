from uuid import UUID
import typer
from typing import Annotated
from rich.table import Table

from cafe_manager.application.use_cases.machine_handlers import (
    CoffeeMachineBuyHandler,
    CoffeeMachineDiscardHandler,
    CoffeeMachineInfoHandler,
    CoffeeMachineResumeHandler,
    CoffeeMachineServiceHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.cli.styles import print_success, print_table
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CLIBusinessError,
    CoffeeMachineNotFoundError,
    CoffeeMachineStateError,
    InsufficientBudgetError,
)
from cafe_manager.infrastructure.sqlite.repositories.equipment_repo import (
    SQLiteCoffeeMachineRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)

from .validation import validate_non_negative
from .custom_types import Money, parse_money

app = typer.Typer(callback=init_context)


@app.command()
def buy(
    ctx: typer.Context,
    price: Annotated[
        Money,
        typer.Option(
            "--price",
            "-p",
            help="Price of the coffee-machine",
            parser=parse_money,
            metavar="MONEY",
        ),
    ],
    model: Annotated[
        str,
        typer.Option("--model", "-m", help="Model of the coffee-machine"),
    ],
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Working cycles amount before maintenance",
            callback=validate_non_negative,
        ),
    ] = 1000,
    account_id: Annotated[
        UUID | None,
        typer.Option(
            "--account",
            "--account-id",
            "-a",
            help="Id of the financial account to take money from",
        ),
    ] = None,
):
    """Buy new coffee-machine"""
    env_path = get_env_path(ctx)
    finance_repo = SQLiteFinanceRepo(env_path)
    machine_repo = SQLiteCoffeeMachineRepo(env_path)
    handler = CoffeeMachineBuyHandler(finance_repo, machine_repo)

    try:
        handler.handle(price=price, model=model, limit=limit, account_id=account_id)

        print_success(f"Coffee-machine of model '{model}' was bought")
    except (AccountNotFoundError, InsufficientBudgetError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def discard(
    ctx: typer.Context,
    machine_id: Annotated[
        int,
        typer.Option(
            "--id",
            help="ID of the coffee-machine",
            callback=validate_non_negative,
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Don't ask your permission before performing",
            prompt="Are you sure you want to discard coffee-machine?",
        ),
    ] = True,
):
    """Discard coffee-machine by ID"""
    env_path = get_env_path(ctx)
    machine_repo = SQLiteCoffeeMachineRepo(env_path)
    handler = CoffeeMachineDiscardHandler(machine_repo)

    try:
        handler.handle(machine_id)

        print_success(f"Coffee-machine with ID {machine_id} was discarded")
    except CoffeeMachineNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info about machines")
    ] = False,
) -> None:
    """Show info about machines"""
    env_path = get_env_path(ctx)
    machine_repo = SQLiteCoffeeMachineRepo(env_path)
    handler = CoffeeMachineInfoHandler(machine_repo)

    machines = handler.handle()

    table = Table(title="coffee-machines")
    table.add_column("", min_width=7)
    table.add_column("id", min_width=10)
    if expanded:
        table.add_column("model", min_width=10)
        table.add_column("state", min_width=10)
        table.add_column("maintenance limit", min_width=15)
        table.add_column("cycles count", min_width=20)

    for i, machine in enumerate(machines):
        params = [i + 1, machine.machine_id]
        if expanded:
            params.extend(
                [
                    machine.model,
                    machine._state,
                    machine.maintenance_limit,
                    machine.cycles_count,
                ]
            )

        str_params = map(str, params)
        table.add_row(*str_params)

    if table.row_count > 0:
        print_table(table)


@app.command()
def service(
    ctx: typer.Context,
    machine_id: Annotated[
        int,
        typer.Option(
            "--id",
            help="ID of the coffee-machine",
            callback=validate_non_negative,
        ),
    ],
):
    """Carry out technical maintenance"""
    env_path = get_env_path(ctx)
    machine_repo = SQLiteCoffeeMachineRepo(env_path)
    handler = CoffeeMachineServiceHandler(machine_repo)

    try:
        handler.handle(machine_id)

        print_success(f"Coffee-machine with ID {machine_id} was given for maintenance")
    except (CoffeeMachineNotFoundError, CoffeeMachineStateError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def resume(
    ctx: typer.Context,
    machine_id: Annotated[
        int,
        typer.Option(
            "--id",
            help="ID of the coffee-machine",
            callback=validate_non_negative,
        ),
    ],
):
    """Resume coffee-machine work after maintenance"""
    env_path = get_env_path(ctx)
    machine_repo = SQLiteCoffeeMachineRepo(env_path)
    handler = CoffeeMachineResumeHandler(machine_repo)

    try:
        handler.handle(machine_id)

        print_success(f"Coffee-machine with ID {machine_id} was taken from maintenance")
    except (CoffeeMachineNotFoundError, CoffeeMachineStateError) as e:
        raise CLIBusinessError(str(e))

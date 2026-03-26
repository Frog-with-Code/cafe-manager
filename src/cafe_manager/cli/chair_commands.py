import typer
from typing import Annotated
from uuid import UUID
from rich.console import Console
from rich.table import Table as RichTable

from cafe_manager.application.use_cases.chair_handlers import (
    ChairBuyHandler,
    ChairDiscardHandler,
    ChairInfoHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CLIBusinessError,
    ChairNotFoundError,
    InsufficientBudgetError,
    TableNotFoundError,
)
from cafe_manager.infrastructure.sqlite.repositories.equipment_repo import (
    SQLiteChairRepo,
    SQLiteTableRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)

from .validation import validate_non_negative
from .custom_types import Money, parse_money

console = Console()
app = typer.Typer(callback=init_context)


@app.command()
def buy(
    ctx: typer.Context,
    price: Annotated[
        Money,
        typer.Option(
            "--price",
            "-p",
            help="Price of the chair",
            parser=parse_money,
            metavar="MONEY",
        ),
    ],
    account_id: Annotated[
        UUID | None,
        typer.Option(
            "--account",
            "--account-id",
            "-a",
            help="ID of the financial account to take money from",
        ),
    ] = None,
):
    """Buy new chair"""
    env_path = get_env_path(ctx)
    chair_repo = SQLiteChairRepo(env_path)
    finance_repo = SQLiteFinanceRepo(env_path)
    handler = ChairBuyHandler(finance_repo=finance_repo, chair_repo=chair_repo)

    try:
        handler.handle(price, account_id)
        console.print("[bold blue]New chair was bought[/bold blue]")
    except (AccountNotFoundError, InsufficientBudgetError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def discard(
    ctx: typer.Context,
    chair_id: Annotated[
        int,
        typer.Option(
            "--id",
            help="ID of the chair",
            callback=validate_non_negative,
        ),
    ],
):
    """Discard chair by its ID"""
    env = get_env_path(ctx)
    chair_repo = SQLiteChairRepo(env)
    table_repo = SQLiteTableRepo(env)
    handler = ChairDiscardHandler(chair_repo, table_repo)

    try:
        handler.handle(chair_id)
        console.print(f"[bold blue]Chair with ID {chair_id} was discarded[/bold blue]")
    except (ChairNotFoundError, TableNotFoundError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expended", "-e", help="Expand info about tables")
    ] = False,
) -> None:
    """Show info about chairs"""
    env_path = get_env_path(ctx)
    table_repo = SQLiteChairRepo(env_path)
    handler = ChairInfoHandler(table_repo)

    chairs = handler.handle()

    rich_table = RichTable(title="chairs")
    rich_table.add_column("", min_width=7)
    rich_table.add_column("id", min_width=10)
    if expanded:
        rich_table.add_column("state", min_width=15)
        rich_table.add_column("table", min_width=15)

    for i, chair in enumerate(chairs):
        params = [i + 1, chair.chair_id]
        if expanded:
            params.extend([chair._state, chair._table_id])

        str_params = map(str, params)
        rich_table.add_row(*str_params)

    if rich_table.row_count > 0:
        console.print(rich_table)

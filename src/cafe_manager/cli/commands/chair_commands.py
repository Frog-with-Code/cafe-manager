from typing import Annotated
from uuid import UUID

import typer
from rich.table import Table as RichTable

from cafe_manager.application.use_cases.chair_handlers import (
    ChairBuyHandler,
    ChairDiscardHandler,
    ChairInfoHandler,
)
from ..context import get_uow, init_context
from ..styles import print_success, print_table
from ..validation import validate_non_negative
from ..custom_types import Money, parse_money

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CLIBusinessError,
    ChairNotFoundError,
    InsufficientBudgetError,
    TableNotFoundError,
)

app = typer.Typer(
    callback=init_context, help="Manage individual chairs and seating assignments"
)


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
    uow = get_uow(ctx)
    handler = ChairBuyHandler(uow)

    try:
        handler.handle(price, account_id)
        print_success("New chair was bought")
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
    uow = get_uow(ctx)
    handler = ChairDiscardHandler(uow)

    try:
        handler.handle(chair_id)
        print_success(f"Chair with ID {chair_id} was discarded")
    except (ChairNotFoundError, TableNotFoundError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info about tables")
    ] = False,
) -> None:
    """Show info about chairs"""
    uow = get_uow(ctx)
    handler = ChairInfoHandler(uow)

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
        print_table(rich_table)

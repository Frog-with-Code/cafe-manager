from typing import Annotated
from uuid import UUID

import typer
from rich.table import Table as RichTable

from .validation import validate_non_negative
from .custom_types import Money, parse_money
from .context import get_uow, init_context
from .styles import print_success, print_table

from cafe_manager.domain.services import SeatingService

from cafe_manager.application.use_cases.table_handlers import (
    AssignChairToTableHandler,
    TableBuyHandler,
    TableDiscardHandler,
    TableFreeHandler,
    TableInfoHandler,
    TableReserveHandler,
)

from cafe_manager.common.exceptions import (
    CLIBusinessError,
    ChairNotFoundError,
    ChairShortageError,
    InsufficientBudgetError,
    AccountNotFoundError,
    TableBusyError,
    TableNotFoundError,
    TablePlacesError,
    TableSuitableNotFoundError,
)


app = typer.Typer(
    callback=init_context, help="Manage cafe tables, reservations, and seating capacity"
)


@app.command()
def buy(
    ctx: typer.Context,
    price: Annotated[
        Money,
        typer.Option(
            "--price",
            "-p",
            help="Price of the table",
            parser=parse_money,
            metavar="MONEY",
        ),
    ],
    seats: Annotated[
        int,
        typer.Option(
            "--seats",
            "-s",
            help="People capacity (max seats) of the table",
            callback=validate_non_negative,
        ),
    ] = 4,
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
    """Buy new n-seats table"""
    uow = get_uow(ctx)
    handler = TableBuyHandler(uow)

    try:
        handler.handle(price=price, seats=seats, account_id=account_id)

        print_success(f"New {seats}-seats table was bought")
    except (AccountNotFoundError, InsufficientBudgetError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def discard(
    ctx: typer.Context,
    table_id: Annotated[
        int,
        typer.Option(
            "--id",
            help="ID of the table",
            callback=validate_non_negative,
        ),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Don't ask your permission before performing",
            prompt="Are you sure you want to discard table?",
        ),
    ] = True,
):
    """Discard table by its ID"""
    uow = get_uow(ctx)
    handler = TableDiscardHandler(uow)

    try:
        handler.handle(table_id)

        print_success(f"Table '{table_id}' was discarded")
    except TableNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info about tables")
    ] = False,
) -> None:
    """Show info about tables"""
    uow = get_uow(ctx)
    handler = TableInfoHandler(uow)

    tables = handler.handle()

    rich_table = RichTable(title="tables")
    rich_table.add_column("")
    rich_table.add_column("id", min_width=10)
    if expanded:
        rich_table.add_column("capacity", min_width=10)
        rich_table.add_column("chairs", min_width=10)
        rich_table.add_column("state", min_width=15)

    for i, table in enumerate(tables):
        params = [i + 1, table.table_id]
        if expanded:
            params.extend([table.max_places, table.chairs_amount, table._state])

        str_params = map(str, params)
        rich_table.add_row(*str_params)

    if rich_table.row_count > 0:
        print_table(rich_table)


@app.command()
def reserve(
    ctx: typer.Context,
    seats: Annotated[
        int,
        typer.Option(
            "--seats", "-s", help="Amount of people", callback=validate_non_negative
        ),
    ],
):
    """Reserve table"""
    uow = get_uow(ctx)
    seating_service = SeatingService()
    handler = TableReserveHandler(uow, seating_service)

    try:
        table_id = handler.handle(seats)

        print_success(f"Table with ID {table_id} was reserved")
    except (
        TableNotFoundError,
        ChairNotFoundError,
        TableSuitableNotFoundError,
        ChairShortageError,
    ) as e:
        raise CLIBusinessError(str(e))


@app.command()
def free(
    ctx: typer.Context,
    table_id: Annotated[
        int,
        typer.Option("--id", help="ID of the table", callback=validate_non_negative),
    ],
):
    """Free reserved or occupied table"""
    uow = get_uow(ctx)
    handler = TableFreeHandler(uow)

    try:
        handler.handle(table_id)

        print_success(f"Table with ID {table_id} was freed")
    except (TableNotFoundError, TableBusyError) as e:
        raise CLIBusinessError(str(e))


@app.command("assign-chair")
def assign_chair(
    ctx: typer.Context,
    table_id: Annotated[
        int,
        typer.Option(
            "--table",
            "--table-id",
            "-t",
            help="ID of the table",
            callback=validate_non_negative,
        ),
    ],
    chair_id: Annotated[
        int,
        typer.Option(
            "--chair",
            "--chair-id",
            "-c",
            help="ID of the chair",
            callback=validate_non_negative,
        ),
    ],
):
    """Assign chair to the table"""
    uow = get_uow(ctx)
    handler = AssignChairToTableHandler(uow)

    try:
        handler.handle(table_id=table_id, chair_id=chair_id)

        print_success(f"Chair {chair_id} was assigned to table {table_id}")
    except (TableNotFoundError, ChairNotFoundError, TablePlacesError) as e:
        raise CLIBusinessError(str(e))

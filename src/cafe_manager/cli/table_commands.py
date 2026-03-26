import typer
from rich.table import Table as RichTable
from typing import Annotated
from uuid import UUID

from cafe_manager.application.use_cases.table_handlers import (
    AssignChairToTableHandler,
    TableBuyHandler,
    TableDiscardHandler,
    TableFreeHandler,
    TableInfoHandler,
    TableReserveHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.cli.styles import print_success, print_table
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
from cafe_manager.domain.services.seating_service import SeatingService
from cafe_manager.infrastructure.sqlite.repositories.equipment_repo import (
    SQLiteChairRepo,
    SQLiteTableRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.order_repo import SQLiteOrderRepo

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
    env_path = get_env_path(ctx)
    finance_repo = SQLiteFinanceRepo(env_path)
    table_repo = SQLiteTableRepo(env_path)
    handler = TableBuyHandler(finance_repo=finance_repo, table_repo=table_repo)

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
    env_path = get_env_path(ctx)
    table_repo = SQLiteTableRepo(env_path)
    chair_repo = SQLiteChairRepo(env_path)
    handler = TableDiscardHandler(table_repo, chair_repo)

    try:
        handler.handle(table_id)

        print_success(f"Table '{table_id}' was discarded")
    except TableNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expended", "-e", help="Expand info about tables")
    ] = False,
) -> None:
    """Show info about tables"""
    env_path = get_env_path(ctx)
    table_repo = SQLiteTableRepo(env_path)
    handler = TableInfoHandler(table_repo)

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
    env_path = get_env_path(ctx)
    table_repo = SQLiteTableRepo(env_path)
    chair_repo = SQLiteChairRepo(env_path)
    seating_service = SeatingService()
    handler = TableReserveHandler(table_repo, chair_repo, seating_service)

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
    table_id: Annotated[int, typer.Option("--id", help="ID of the table")],
):
    """Free reserved or occupied table"""
    env_path = get_env_path(ctx)
    table_repo = SQLiteTableRepo(env_path)
    chair_repo = SQLiteChairRepo(env_path)
    order_repo = SQLiteOrderRepo(env_path)
    handler = TableFreeHandler(
        table_repo=table_repo, chair_repo=chair_repo, order_repo=order_repo
    )

    try:
        handler.handle(table_id)

        print_success(f"Table with ID {table_id} was freed")
    except (TableNotFoundError, TableBusyError) as e:
        raise CLIBusinessError(str(e))


@app.command("assign-chair")
def assign_chair(
    ctx: typer.Context,
    table_id: Annotated[
        int, typer.Option("--table", "--table-id", "-t", help="ID of the table")
    ],
    chair_id: Annotated[
        int, typer.Option("--chair", "--chair-id", "-c", help="ID of the chair")
    ],
):
    """Assign chair to the table"""
    env_path = get_env_path(ctx)
    table_repo = SQLiteTableRepo(env_path)
    chair_repo = SQLiteChairRepo(env_path)
    handler = AssignChairToTableHandler(table_repo, chair_repo)

    try:
        handler.handle(table_id=table_id, chair_id=chair_id)

        print_success(f"Chair {chair_id} was assigned to table {table_id}")
    except (TableNotFoundError, ChairNotFoundError, TablePlacesError) as e:
        raise CLIBusinessError(str(e))

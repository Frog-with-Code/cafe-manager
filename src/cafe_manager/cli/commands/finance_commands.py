from datetime import datetime
from uuid import UUID
from typing import Annotated

import typer
from rich.table import Table

from ..context import get_uow, init_context
from ..custom_types import parse_money, Money
from ..styles import print_info, print_success, print_table
from ..validation import validate_non_negative

from cafe_manager.application.use_cases.finance_handlers import (
    FinanceHistoryHandler,
    FinanceInvestHandler,
    FinanceSetPrimaryHandler,
    FinanceStatsHandler,
)

from cafe_manager.common.exceptions import AccountNotFoundError, CLIBusinessError

app = typer.Typer(
    callback=init_context, help="Track financial operations, budget, and statistics"
)


@app.command()
def invest(
    ctx: typer.Context,
    money: Annotated[
        Money,
        typer.Option(
            "--money",
            "-m",
            parser=parse_money,
            metavar="MONEY",
            help="Amount of money to invest",
        ),
    ],
    account_id: Annotated[
        UUID | None,
        typer.Option(
            "--account",
            "--account-id",
            "-a",
            help="ID of the target financial account",
        ),
    ] = None,
    description: Annotated[
        str, typer.Option("--description", "-d", help="Description of the transaction")
    ] = "Investment",
):
    """Invest money to the cafe budget"""
    uow = get_uow(ctx)
    handler = FinanceInvestHandler(uow)

    try:
        handler.handle(money, account_id, description)
        print_success("Money were invested to the account")
    except AccountNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def stats(
    сtx: typer.Context,
    account_id: Annotated[
        UUID | None,
        typer.Option(
            "--account",
            "--account-id",
            "-a",
            help="Id of the target financial account",
        ),
    ] = None,
    start: Annotated[
        datetime | None, typer.Argument(help="Start date for statistics")
    ] = None,
    end: Annotated[
        datetime | None, typer.Argument(help="End date for statistics")
    ] = None,
):
    """Show statistics about budget, income, outcome and profit"""
    uow = get_uow(сtx)
    handler = FinanceStatsHandler(uow)

    try:
        stats = handler.handle(account_id=account_id, start_date=start, end_date=end)

        w = 10
        print_info(f"{'ID:':<{w}} {stats['id']}")
        print_info(f"{'Balance:':<{w}} {stats['balance']}")
        print_info(f"{'Income:':<{w}} {stats['income']}")
        print_info(f"{'Expense:':<{w}} {stats['expense']}")

        sign = "-" if stats["is_loss"] else "+"
        print_info(f"{'Profit:':<{w}} {sign}{stats['profit_abs']}")
    except AccountNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def history(
    ctx: typer.Context,
    account_id: Annotated[
        UUID | None,
        typer.Option(
            "--account",
            "--account-id",
            "-a",
            help="ID of the target financial account",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Number of latest transactions to show",
            callback=validate_non_negative,
        ),
    ] = 5,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info about transactions")
    ] = False,
) -> None:
    """Show info about n latest transactions"""
    uow = get_uow(ctx)
    handler = FinanceHistoryHandler(uow)

    try:
        history = handler.handle(account_id, limit)
    except AccountNotFoundError as e:
        raise CLIBusinessError(str(e))

    table = Table(title="history")
    table.add_column("")
    table.add_column("money")
    table.add_column("type")
    if expanded:
        table.add_column("id")
        table.add_column("time")
        table.add_column("description")

    for i, transaction in enumerate(history):
        params = [i + 1, transaction.money, transaction.transaction_type]
        if expanded:
            params.extend(
                [
                    transaction.transaction_id,
                    transaction.time,
                    transaction.description,
                ]
            )

        str_params = map(str, params)
        table.add_row(*str_params)

    if table.row_count > 0:
        print_table(table)


@app.command("set-primary")
def set_primary(
    ctx: typer.Context,
    account_id: Annotated[
        UUID,
        typer.Argument(
            help="ID of the target financial account",
        ),
    ],
):
    """Set account as primary to proceed financial operations without explicit ID"""
    uow = get_uow(ctx)
    handler = FinanceSetPrimaryHandler(uow)

    try:
        handler.handle(account_id)
        print_success(f"Account was set as primary")
    except AccountNotFoundError as e:
        raise CLIBusinessError(str(e))

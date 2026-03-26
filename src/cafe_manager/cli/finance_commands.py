from datetime import datetime
from uuid import UUID
import typer
from typing import Annotated
from rich.console import Console
from rich.table import Table

from cafe_manager.application.use_cases.finance_handlers import (
    FinanceHistoryHandler,
    FinanceInvestHandler,
    FinanceSetPrimaryHandler,
    FinanceStatsHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.cli.custom_types import parse_money, Money
from cafe_manager.cli.validation import validate_non_negative
from cafe_manager.common.exceptions import AccountNotFoundError, CLIBusinessError
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)

console = Console()
app = typer.Typer(callback=init_context)


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
    env_path = get_env_path(ctx)
    finance_repo = SQLiteFinanceRepo(env_path)
    handler = FinanceInvestHandler(finance_repo)

    try:
        handler.handle(money, account_id, description)
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
    env_path = get_env_path(сtx)
    finance_repo = SQLiteFinanceRepo(env_path)
    handler = FinanceStatsHandler(finance_repo)

    try:
        stats = handler.handle(account_id=account_id, start_date=start, end_date=end)

        w = 10
        console.print(f"[bold blue]{'ID:':<{w}} {stats['id']}[/bold blue]")
        console.print(f"[bold blue]{'Balance:':<{w}} {stats['balance']}[/bold blue]")
        console.print(f"[bold blue]{'Income:':<{w}} {stats['income']}[/bold blue]")
        console.print(f"[bold blue]{'Expense:':<{w}} {stats['expense']}[/bold blue]")

        sign = "-" if stats["is_loss"] else "+"
        console.print(
            f"[bold blue]{'Profit:':<{w}} {sign}{stats['profit_abs']}[/bold blue]"
        )
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
    env_path = get_env_path(ctx)
    finance_repo = SQLiteFinanceRepo(env_path)
    handler = FinanceHistoryHandler(finance_repo)

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
        console.print(table)


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
    env_path = get_env_path(ctx)
    finance_repo = SQLiteFinanceRepo(env_path)
    handler = FinanceSetPrimaryHandler(finance_repo)

    try:
        handler.handle(account_id)
    except AccountNotFoundError as e:
        raise CLIBusinessError(str(e))

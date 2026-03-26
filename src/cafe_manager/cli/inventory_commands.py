from uuid import UUID
import typer
from typing import Annotated
from rich.table import Table

from cafe_manager.application.use_cases.inventory_handlers import (
    InventoryAddHandler,
    InventoryInfoHandler,
    InventoryRemoveHandler,
    InventorySupplyHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.cli.custom_types import parse_money, Money
from cafe_manager.cli.styles import print_success, print_table
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CLIBusinessError,
    IngredientExistsError,
    IngredientNotFoundError,
    InsufficientBudgetError,
)
from cafe_manager.domain.entities.menu import Unit
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.inventory_repo import (
    SQLiteInventoryRepo,
)

app = typer.Typer(callback=init_context)


@app.command("add-ingredient")
def add_ingredient(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the ingredient")],
    unit: Annotated[Unit, typer.Option("--unit", "-u", help="Unit of the ingredient")],
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite", "-o", help="Overwrite information about inventory item"
        ),
    ] = False,
):
    """Add new ingredient to the inventory"""
    env_path = get_env_path(ctx)
    inventory_repo = SQLiteInventoryRepo(env_path)
    handler = InventoryAddHandler(inventory_repo)

    try:
        handler.handle(name, unit, overwrite)

        print_success(f"'{name}' was added to the inventory")
    except IngredientExistsError as e:
        raise CLIBusinessError(str(e))


@app.command("remove-ingredient")
def remove_ingredient(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the ingredient")],
):
    """Remove ingredient with all its stocks from the inventory"""
    env_path = get_env_path(ctx)
    inventory_repo = SQLiteInventoryRepo(env_path)
    handler = InventoryRemoveHandler(inventory_repo)

    try:
        handler.handle(name)

        print_success(f"'{name}' was removed from the inventory")
    except IngredientNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info table about inventory")
    ] = False,
):
    """Show info about inventory items"""
    env_path = get_env_path(ctx)
    inventory_repo = SQLiteInventoryRepo(env_path)
    handler = InventoryInfoHandler(inventory_repo)

    ingredients = handler.handle()

    table = Table(title="ingredients")
    table.add_column("")
    table.add_column("name", min_width=20)
    if expanded:
        table.add_column("amount", min_width=20)
        table.add_column("unit")

    for i, (ingr, amount) in enumerate(ingredients.items()):
        params = [i + 1, ingr.name]
        if expanded:
            params.extend([amount, ingr.unit])

        str_params = map(str, params)
        table.add_row(*str_params)

    if table.row_count > 0:
        print_table(table)


@app.command()
def supply(
    ctx: typer.Context,
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Name of the ingredient"),
    ],
    quantity: Annotated[
        float, typer.Option("--quantity", "-q", help="Quantity of ingredients")
    ],
    price: Annotated[
        Money,
        typer.Option(
            "--price",
            "-p",
            help="Total price of the operation",
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
            help="ID of the account to take money from",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", prompt=f"Are you sure you want to buy ingredient?"
        ),
    ] = True,
):
    """Supply inventory with existing ingredient"""
    env_path = get_env_path(ctx)
    inventory_repo = SQLiteInventoryRepo(env_path)
    finance_repo = SQLiteFinanceRepo(env_path)
    handler = InventorySupplyHandler(inventory_repo, finance_repo)

    try:
        handler.handle(name=name, amount=quantity, price=price, account_id=account_id)
        print_success(f"Inventory was supplied by '{name}' in amount of {quantity}")
    except (
        AccountNotFoundError,
        IngredientNotFoundError,
        InsufficientBudgetError,
    ) as e:
        raise CLIBusinessError(str(e))

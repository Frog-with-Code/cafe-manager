import typer
from typing import Annotated
from rich.table import Table
from rich.console import Console

from cafe_manager.application.use_cases.menu_handlers import (
    MenuAddItemHandler,
    MenuInfoHandler,
    MenuItemRemoveHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.common.exceptions import (
    CLIBusinessError,
    MenuItemExistsError,
    MenuItemNotFoundError,
)
from cafe_manager.domain.entities.menu import MenuItemCategory
from cafe_manager.infrastructure.sqlite.repositories.menu_repo import SQLiteMenuRepo
from cafe_manager.domain.entities.menu import Unit

from .validation import validate_non_negative
from .custom_types import Money, parse_money

console = Console()
err_console = Console(stderr=True)
app = typer.Typer(callback=init_context)


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info table about menu")
    ] = False,
):
    """Show info about menu items"""
    env_path = get_env_path(ctx)
    menu_repo = SQLiteMenuRepo(env_path)
    handler = MenuInfoHandler(menu_repo)

    grouped_items = handler.handle()

    for menu_type, items in grouped_items.items():
        table = Table(title=f"{str(menu_type)}")

        table.add_column("name", min_width=15)

        if expanded:
            table.add_column("price", min_width=15)
            table.add_column("category", min_width=15)

        for i in items:
            params = [i.name]
            if expanded:
                params.extend([str(i.price), str(i.category)])

            table.add_row(*params)

        console.print(table)


@app.command("add-item")
def add_item(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the menu item")],
    price: Annotated[
        Money,
        typer.Option(
            "--price",
            "-p",
            help="Price of the menu item",
            parser=parse_money,
            metavar="MONEY",
        ),
    ],
    category: Annotated[
        MenuItemCategory,
        typer.Option("--category", "-c", help="Category of the menu item"),
    ],
    milk_foam: Annotated[
        bool,
        typer.Option(
            "--milk-foam", "-m", help="Milk foam is required for the menu item"
        ),
    ] = False,
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", "-o", help="Overwrite information about menu item"),
    ] = False,
):
    """Add new item to the menu"""
    ingredients: dict[str, dict[str, float]] = {}
    while True:
        print()
        ing_name = typer.prompt("Enter ingredient (or enter 'q' to quit)", type=str)

        if ing_name in ("q", "Q"):
            break

        if ingredients.get(ing_name, None) is not None:
            err_console.print(
                "[bold red]Don't enter the same ingredients several times[/bold red]"
            )
            continue

        ing_unit = typer.prompt("Enter unit of the ingredient", type=str)

        try:
            Unit(ing_unit)
        except ValueError:
            values = [item.value for item in Unit]
            err_console.print(
                f"[bold red]Unknown unit of the ingredient.[bold red] \n [bold yellow]Only {values} are allowed[/bold yellow]"
            )
            continue

        ing_amount = typer.prompt("Enter amount of the ingredient", type=float)

        try:
            validate_non_negative(ing_amount)
        except typer.BadParameter:
            err_console.print("[bold red]Ingredient amount must be positive[/bold red]")
            continue

        ingredients[ing_name] = {"unit": ing_unit, "amount": ing_amount}

    if not ingredients:
        raise CLIBusinessError("Impossible to add menu item without ingredients")

    env_path = get_env_path(ctx)
    menu_repo = SQLiteMenuRepo(env_path)
    handler = MenuAddItemHandler(menu_repo)

    try:
        handler.handle(
            name=name,
            price=price,
            category=category,
            ingredients_data=ingredients,
            overwrite=overwrite,
        )
        console.print(f"[bold blue]{name} was added to the menu[/bold blue]")
    except MenuItemExistsError as e:
        raise CLIBusinessError(str(e))


@app.command("remove-item")
def remove_item(
    ctx: typer.Context,
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Name of the menu item"),
    ],
):
    """Remove menu items from the menu"""
    env_path = get_env_path(ctx)
    menu_repo = SQLiteMenuRepo(env_path)
    handler = MenuItemRemoveHandler(menu_repo)

    try:
        handler.handle(name)
        console.print(f"[bold blue]{name} was removed from the menu[/bold blue]")
    except MenuItemNotFoundError as e:
        raise CLIBusinessError(str(e))

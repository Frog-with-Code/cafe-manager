from typing import Annotated

import typer
from rich.table import Table

from .context import get_uow, init_context
from .styles import print_error, print_success, print_table
from .validation import validate_non_negative
from .custom_types import Money, parse_money

from cafe_manager.domain.entities.menu import MenuItemCategory

from cafe_manager.application.use_cases.menu_handlers import (
    MenuAddItemHandler,
    MenuInfoHandler,
    MenuItemRemoveHandler,
    MenuListIngredientsHandler,
)

from cafe_manager.common.exceptions import (
    CLIBusinessError,
    IngredientNotFoundError,
    MenuItemExistsError,
    MenuItemNotFoundError,
)


app = typer.Typer(
    callback=init_context, help="Configure menu items, prices, and recipes"
)


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info table about menu")
    ] = False,
):
    """Show info about menu items"""
    uow = get_uow(ctx)
    handler = MenuInfoHandler(uow)

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

        print_table(table)


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
    overwrite: Annotated[
        bool,
        typer.Option("--overwrite", "-o", help="Overwrite information about menu item"),
    ] = False,
):
    """Add new item to the menu"""
    ingredients: dict[str, float] = {}
    while True:
        print()
        ing_name = typer.prompt("Enter ingredient (or enter 'q' to quit)", type=str)

        if ing_name in ("q", "Q"):
            break

        if ingredients.get(ing_name, None) is not None:
            print_error("Don't enter the same ingredients several times")
            continue

        ing_amount = typer.prompt("Enter amount of the ingredient", type=float)
        try:
            validate_non_negative(ing_amount)
        except typer.BadParameter:
            print_error("Ingredient amount must be positive")
            continue

        ingredients[ing_name] = ing_amount

    if not ingredients:
        raise CLIBusinessError("Impossible to add menu item without ingredients")

    uow = get_uow(ctx)
    handler = MenuAddItemHandler(uow)

    try:
        handler.handle(
            name=name,
            price=price,
            category=category,
            ingredients_data=ingredients,
            overwrite=overwrite,
        )

        print_success(f"{name} was added to the menu")
    except (MenuItemExistsError, IngredientNotFoundError) as e:
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
    uow = get_uow(ctx)
    handler = MenuItemRemoveHandler(uow)

    try:
        handler.handle(name)

        print_success(f"{name} was removed from the menu")
    except MenuItemNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command("list-ingredients")
def list_ingredients(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the menu item")],
):
    """List ingredients of the menu item"""
    uow = get_uow(ctx)
    handler = MenuListIngredientsHandler(uow)

    try:
        ingredients = handler.handle(name)

        table = Table(title="ingredients", *["", "name", "amount"])

        for i, (ingr, amount) in enumerate(ingredients.items()):
            params = [i + 1, ingr.name, amount]
            str_params = map(str, params)

            table.add_row(*str_params)

        if table.row_count > 0:
            print_table(table)

    except MenuItemNotFoundError as e:
        raise CLIBusinessError(str(e))

from re import I
import typer
from typing import Annotated
from rich.table import Table
from rich.console import Console

from cafe_manager.applications.use_cases.kitchen_handlers import (
    KitchenListPending,
    KitchenReadyHandler,
    KitchenStartHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.common.exceptions import (
    CLIBusinessError,
    EmployeeNotFoundError,
    KitchenOverloadError,
    OrderNotFoundError,
    OrderStateError,
)
from cafe_manager.domain.services.ingredient_calculator import IngredientCalculator
from cafe_manager.infrastructure.sqlite.repositories.equipment_repo import (
    SQLiteCoffeeMachineRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.inventory_repo import (
    SQLiteInventoryRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.order_repo import SQLiteOrderRepo
from cafe_manager.infrastructure.sqlite.repositories.people_repo import (
    SQLiteEmployeeRepo,
)

console = Console()
app = typer.Typer(callback=init_context)


@app.command("list-pending")
def show_list_pending(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info about orders")
    ] = False,
):
    """Shows query of paid orders"""
    env_path = get_env_path(ctx)
    order_repo = SQLiteOrderRepo(env_path)
    handler = KitchenListPending(order_repo)

    orders = handler.handle()
    table = Table(title="pending orders")
    table.add_column("", min_width=7)
    table.add_column("id", min_width=10)
    table.add_column("paid at", min_width=20)
    if expanded:
        table.add_column("price", min_width=15)
        table.add_column("table id", min_width=10)
        table.add_column("client id", min_width=15)
        table.add_column("created at", min_width=20)

    for i, order in enumerate(orders):
        params = [i + 1, order.order_id, order.paid_at]
        if expanded:
            params.extend(
                [
                    order.total_price,
                    order.table_id,
                    order.client_id,
                    order.created_at,
                ]
            )

        str_params = map(str, params)
        table.add_row(*str_params)

    if table.row_count > 0:
        console.print(table)


@app.command()
def start(
    ctx: typer.Context,
    employee_id: Annotated[
        str | None,
        typer.Option("--id", help="Id of the order to start cooking"),
    ] = None,
):
    """Start cooking oldest paid order"""
    env_path = get_env_path(ctx)
    order_repo = SQLiteOrderRepo(env_path)
    employee_repo = SQLiteEmployeeRepo(env_path)
    inventory_repo = SQLiteInventoryRepo(env_path)
    machine_repo = SQLiteCoffeeMachineRepo(env_path)
    ingredient_calculator = IngredientCalculator()
    handler = KitchenStartHandler(
        order_repo=order_repo,
        employee_repo=employee_repo,
        inventory_repo=inventory_repo,
        machine_repo=machine_repo,
        ingredient_calculator=ingredient_calculator,
    )

    try:
        order_id = handler.handle(employee_id)
        if order_id is None:
            console.print("[bold blue]No paid orders[/bold blue]")
        else:
            console.print(
                f"[bold blue]Order with ID {order_id} was handed over for cooking[/bold blue]"
            )
    except (EmployeeNotFoundError, KitchenOverloadError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def complete(
    ctx: typer.Context,
    order_id: Annotated[
        str,
        typer.Option("--id", help="Id of the order to complete"),
    ],
):
    """Complete order in progress"""
    env_path = get_env_path(ctx)
    order_repo = SQLiteOrderRepo(env_path)
    handler = KitchenReadyHandler(order_repo)

    try:
        handler.handle(order_id)
    except (OrderNotFoundError, OrderStateError) as e:
        raise CLIBusinessError(str(e))

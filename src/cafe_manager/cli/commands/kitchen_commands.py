from re import I
from typing import Annotated

import typer
from rich.table import Table

from ..context import get_uow, init_context
from ..styles import print_success, print_table, print_warning

from cafe_manager.application.use_cases.kitchen_handlers import (
    KitchenListPending,
    KitchenReadyHandler,
    KitchenStartHandler,
)

from cafe_manager.infrastructure.factory import get_ingredient_calculator

from cafe_manager.common.exceptions import (
    CLIBusinessError,
    EmployeeNotFoundError,
    KitchenOverloadError,
    OrderNotFoundError,
    OrderStateError,
)

app = typer.Typer(
    callback=init_context,
    help="Kitchen operations, cooking queue, and order fulfillment",
)


@app.command("list-pending")
def show_list_pending(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info about orders")
    ] = False,
):
    """Shows query of paid orders"""
    uow = get_uow(ctx)
    handler = KitchenListPending(uow)

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
        print_table(table)


@app.command()
def start(
    ctx: typer.Context,
    employee_id: Annotated[
        str | None,
        typer.Option("--id", help="ID of the order to start cooking"),
    ] = None,
):
    """Start cooking oldest paid order"""
    uow = get_uow(ctx)
    ingredient_calculator = get_ingredient_calculator()
    handler = KitchenStartHandler(
        uow=uow,
        ingredient_calculator=ingredient_calculator,
    )

    try:
        order_id, employee_id, machine_id = handler.handle(employee_id)
        if order_id is None:
            print_warning("No pending orders")
        else:
            w = 5
            machine_text = f"{'Machine:':{w}} {machine_id}" if machine_id else ""
            print_success(
                f"Order with ID {order_id} was handed over for cooking\n{'Employee:':<{w}} {employee_id}\n{machine_text}"
            )
    except (EmployeeNotFoundError, KitchenOverloadError) as e:
        raise CLIBusinessError(str(e))


@app.command()
def complete(
    ctx: typer.Context,
    order_id: Annotated[
        str,
        typer.Option("--id", help="ID of the order to complete"),
    ],
):
    """Complete order in progress"""
    uow = get_uow(ctx)
    handler = KitchenReadyHandler(uow)

    try:
        handler.handle(order_id)

        print_success("Order was completed")
    except (OrderNotFoundError, OrderStateError) as e:
        raise CLIBusinessError(str(e))

from uuid import UUID
from typing import Annotated

import typer
from rich.table import Table

from ..styles import print_success, print_table
from ..validation import validate_item_format, validate_non_negative
from ..custom_types import Money, parse_money
from ..context import get_uow, init_context

from cafe_manager.application.use_cases.order_handlers import (
    OrderCreateHandler,
    OrderInfoHandler,
    OrderPayHandler,
    OrderServeHandler,
)

from cafe_manager.infrastructure.factory import get_id_generator, get_payment_service, get_ingredient_calculator

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CLIBusinessError,
    ClientNotFoundError,
    IngredientNotFoundError,
    InsufficientBudgetError,
    InsufficientStocksError,
    MenuItemNotFoundError,
    MenuItemRepeatError,
    OrderNotFoundError,
    OrderStateError,
    TableNotFoundError,
    TableStateError,
)


app = typer.Typer(
    callback=init_context, help="Manage customer orders, payments, and serving"
)


@app.command()
def create(
    ctx: typer.Context,
    items: Annotated[
        list[str],
        typer.Argument(
            callback=lambda items: [validate_item_format(i) for i in items],
            help="Menu items in format name:amount",
        ),
    ],
    table_id: Annotated[
        int | None,
        typer.Option(
            "--table",
            "--table-id",
            "-t",
            help="ID of the reserved table",
            callback=validate_non_negative,
        ),
    ] = None,
    continue_session: Annotated[
        bool,
        typer.Option(
            "--continue", "-c", help="Add order to the already occupied table"
        ),
    ] = False,
):
    """Creates new order"""
    uow = get_uow(ctx)
    ingredient_calculator = get_ingredient_calculator()
    id_generator = get_id_generator()
    handler = OrderCreateHandler(
        uow=uow,
        ingredient_calculator=ingredient_calculator,
        id_generator=id_generator,
    )

    try:
        order_id = handler.handle(items, table_id, continue_session)  # type: ignore

        print_success(f"New order with ID {order_id} was created")
    except (
        TableNotFoundError,
        TableStateError,
        MenuItemNotFoundError,
        MenuItemRepeatError,
        IngredientNotFoundError,
        InsufficientStocksError,
        RuntimeError,
    ) as e:
        raise CLIBusinessError(str(e))


@app.command()
def pay(
    ctx: typer.Context,
    order_id: Annotated[
        str,
        typer.Option("--id", help="ID of the order to pay for"),
    ],
    price: Annotated[
        Money,
        typer.Option(
            "--price",
            "-p",
            help="Money to pay for the order",
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
    client_id: Annotated[
        str | None,
        typer.Option("--client", "--client-id", "-c", help="ID of the client"),
    ] = None,
):
    """Pay the order"""
    uow = get_uow(ctx)
    payment_service = get_payment_service()
    handler = OrderPayHandler(
        uow=uow,
        payment_service=payment_service,
    )

    try:
        handler.handle(
            order_id=order_id,
            cash_provided=price,
            account_id=account_id,
            client_id=client_id,
        )

        print_success("Order was paid")
    except (
        OrderNotFoundError,
        OrderStateError,
        AccountNotFoundError,
        ClientNotFoundError,
        InsufficientBudgetError,
    ) as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info table about orders")
    ] = False,
):
    """Show info about active orders"""
    uow = get_uow(ctx)
    handler = OrderInfoHandler(uow)

    orders = handler.handle()
    table = Table(title="active orders", *("", "id", "state"))

    if expanded:
        table.add_column("created at")
        table.add_column("paid at")
        table.add_column("price")
        table.add_column("table")
        table.add_column("client")
        table.add_column("employee")
    for i, order in enumerate(orders):
        params = [i + 1, order.order_id, order._state]
        if expanded:
            params.extend(
                [
                    order.created_at,
                    order.paid_at,
                    order.total_price,
                    order.table_id,
                    order.client_id,
                    order.employee_id,
                ]
            )

        str_params = map(str, params)
        table.add_row(*str_params)

    if table.row_count > 0:
        print_table(table)


@app.command()
def serve(
    ctx: typer.Context,
    order_id: Annotated[str, typer.Option("--id", help="ID of the order to serve")],
):
    """Serve the order"""
    uow = get_uow(ctx)
    handler = OrderServeHandler(uow)

    try:
        handler.handle(order_id)

        print_success("Order was served")
    except (OrderNotFoundError, OrderStateError) as e:
        raise CLIBusinessError(str(e))

from uuid import UUID
import typer
from typing import Annotated
from rich.console import Console
from rich.table import Table

from cafe_manager.applications.use_cases.order_handlers import (
    OrderCreateHandler,
    OrderInfoHandler,
    OrderPayHandler,
    OrderServeHandler,
)
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
from cafe_manager.domain.services.ingredient_calculator import IngredientCalculator
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.domain.services.payment_service import PaymentService
from cafe_manager.infrastructure.sqlite.repositories.equipment_repo import (
    SQLiteChairRepo,
    SQLiteTableRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import (
    SQLiteFinanceRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.inventory_repo import (
    SQLiteInventoryRepo,
)
from cafe_manager.infrastructure.sqlite.repositories.menu_repo import SQLiteMenuRepo
from cafe_manager.infrastructure.sqlite.repositories.order_repo import SQLiteOrderRepo
from cafe_manager.infrastructure.sqlite.repositories.people_repo import (
    SQLiteClientRepo,
    SQLiteEmployeeRepo,
)

from .validation import validate_item_format, validate_non_negative
from .custom_types import Money, parse_money
from .context import get_env_path, init_context, BASE_DIR

app = typer.Typer(help="Commands for order management", callback=init_context)
console = Console()


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
    table: Annotated[
        int | None,
        typer.Option(
            "--table",
            "--table-id",
            "-t",
            help="Id of the reserved table",
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
    env_path = get_env_path(ctx)
    order_repo = SQLiteOrderRepo(env_path)
    inventory_repo = SQLiteInventoryRepo(env_path)
    menu_repo = SQLiteMenuRepo(env_path)
    table_repo = SQLiteTableRepo(env_path)
    chair_repo = SQLiteChairRepo(env_path)
    ingredient_calculator = IngredientCalculator()
    id_generator = IDGeneratingService()
    handler = OrderCreateHandler(
        order_repo=order_repo,
        inventory_repo=inventory_repo,
        menu_repo=menu_repo,
        table_repo=table_repo,
        chair_repo=chair_repo,
        ingredient_calculator=ingredient_calculator,
        id_generator=id_generator,
    )

    try:
        order_id = handler.handle(items, table, continue_session)  # type: ignore
        console.print(
            f"[bold blue]New order with ID {order_id} was created[/bold blue]"
        )
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
    order: Annotated[
        str,
        typer.Option("--order", "--order-id", "-o", help="Id of the order to pay for"),
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
    account: Annotated[
        UUID | None,
        typer.Option(
            "--account",
            "--account-id",
            "-a",
            help="Id of the financial account to take money from",
        ),
    ] = None,
    client: Annotated[
        str | None,
        typer.Option("--client", "--client-id", "-c", help="Id of the client"),
    ] = None,
):
    """Pay the order"""
    env_path = get_env_path(ctx)
    order_repo = SQLiteOrderRepo(env_path)
    finance_repo = SQLiteFinanceRepo(env_path)
    client_repo = SQLiteClientRepo(env_path)
    payment_service = PaymentService()
    handler = OrderPayHandler(
        order_repo=order_repo,
        finance_repo=finance_repo,
        client_repo=client_repo,
        payment_service=payment_service,
    )

    try:
        handler.handle(
            order_id=order, cash_provided=price, account_id=account, client_id=client
        )
        console.print("[bold blue]Order was paid[/bold blue]")
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
    env_path = get_env_path(ctx)
    order_repo = SQLiteOrderRepo(env_path)
    handler = OrderInfoHandler(order_repo)

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
        console.print(table)


@app.command()
def serve(
    ctx: typer.Context,
    order_id: Annotated[str, typer.Option("--id", help="ID of the order to serve")],
):
    """Serve the order"""
    env_path = get_env_path(ctx)
    order_repo = SQLiteOrderRepo(env_path)
    employee_repo = SQLiteEmployeeRepo(env_path)
    handler = OrderServeHandler(order_repo, employee_repo)

    try:
        handler.handle(order_id)
    except (OrderNotFoundError, OrderStateError) as e:
        raise CLIBusinessError(str(e))

from typing import Annotated

import typer
from rich.table import Table

from .context import get_env_path, init_context
from .styles import print_info, print_success, print_table

from cafe_manager.domain.services import IDGeneratingService

from cafe_manager.application.use_cases.client_handlers import (
    ClientCreateHandler,
    ClientInfoHandler,
    ClientListHandler,
)

from cafe_manager.infrastructure.sqlite.repositories import SQLiteClientRepo

from cafe_manager.common.exceptions import CLIBusinessError, ClientNotFoundError


app = typer.Typer(callback=init_context)


@app.command()
def create(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the client")],
) -> None:
    """Create new client account"""
    env_path = get_env_path(ctx)
    client_repo = SQLiteClientRepo(env_path)
    id_generator = IDGeneratingService()
    handler = ClientCreateHandler(client_repo, id_generator)

    try:
        client_id = handler.handle(name)
        print_success(f"New client with ID '{client_id}' was created")
    except RuntimeError as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    client_id: Annotated[
        str,
        typer.Option("--id", help="ID of the target client"),
    ],
):
    """Show info about the client"""
    env_path = get_env_path(ctx)
    client_repo = SQLiteClientRepo(env_path)
    handler = ClientInfoHandler(client_repo)

    try:
        client = handler.handle(client_id)

        w = 20
        print_info(f"{'ID:':<{w}} {client.client_id}")
        print_info(f"{'Name:':<{w}} {client.name}")
        print_info(f"{'Total spent:':<{w}} {client.total_spent}")
        print_info(f"{'Orders amount:':<{w}} {client.orders_amount}")
        print_info(f"{'Registered at:':<{w}} {client.registered_at}")
    except ClientNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command("list")
def list_by_name(
    ctx: typer.Context,
    name: Annotated[
        str,
        typer.Option("--name", "-n", help="Name of the target clients"),
    ],
):
    """Show list of clients by their name"""
    env_path = get_env_path(ctx)
    client_repo = SQLiteClientRepo(env_path)
    handler = ClientListHandler(client_repo)

    clients = handler.handle(name)

    table = Table(title="orders", *["", "id", "name"])

    for i, client in enumerate(clients):
        params = [i + 1, client.client_id, client.name]
        str_params = map(str, params)

        table.add_row(*str_params)

    if table.row_count > 0:
        print_table(table)

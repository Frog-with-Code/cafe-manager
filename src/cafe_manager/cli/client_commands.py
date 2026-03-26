import typer
from typing import Annotated
from rich.console import Console

from cafe_manager.application.use_cases.client_handlers import (
    ClientCreateHandler,
    ClientInfoHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.common.exceptions import CLIBusinessError, ClientNotFoundError
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.infrastructure.sqlite.repositories.people_repo import SQLiteClientRepo


app = typer.Typer(callback=init_context)
console = Console()


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
        console.print(f"[bold blue]New client with ID '{client_id}' was created[/bold blue]")
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
        console.print(f"[bold blue]{'ID:':<{w}} {client.client_id}[/bold blue]")
        console.print(f"[bold blue]{'Name:':<{w}} {client.name}[/bold blue]")
        console.print(f"[bold blue]{'Total spent:':<{w}} {client.total_spent}[/bold blue]")
        console.print(f"[bold blue]{'Orders amount:':<{w}} {client.orders_amount}[/bold blue]")
        console.print(f"[bold blue]{'Registered at:':<{w}} {client.registered_at}[/bold blue]")
    except ClientNotFoundError as e:
        raise CLIBusinessError(str(e))

    
    

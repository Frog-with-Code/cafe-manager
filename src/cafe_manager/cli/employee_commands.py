import typer
from typing import Annotated
from rich.console import Console
from rich.table import Table

from cafe_manager.applications.use_cases.employee_handlers import (
    EmployeeFireHandler,
    EmployeeHireHandler,
    EmployeeInfoHandler,
)
from cafe_manager.cli.context import get_env_path, init_context
from cafe_manager.common.exceptions import CLIBusinessError, EmployeeNotFoundError
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.infrastructure.sqlite.repositories.people_repo import (
    SQLiteEmployeeRepo,
)

console = Console()
app = typer.Typer(callback=init_context)


@app.command()
def hire(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the employee")],
):
    """Hire new employee"""
    env_path = get_env_path(ctx)
    employee_repo = SQLiteEmployeeRepo(env_path)
    id_generator = IDGeneratingService()
    handler = EmployeeHireHandler(
        employee_repo=employee_repo, id_generator=id_generator
    )

    try:
        handler.handle(name)
        console.print(f"[bold blue]{name} was hired as new employee[/bold blue]")
    except RuntimeError as e:
        raise CLIBusinessError(str(e))


@app.command()
def fire(
    ctx: typer.Context,
    employee_id: Annotated[
        str,
        typer.Option("--employee", "--employee-id", "-e", help="Id of the employee"),
    ],
):
    """Fire employee by his ID"""
    env_path = get_env_path(ctx)
    employee_repo = SQLiteEmployeeRepo(env_path)
    handler = EmployeeFireHandler(employee_repo)

    try:
        handler.handle(employee_id)
        console.print(
            f"[bold blue]Employee with id {employee_id} was fired[/bold blue]"
        )
    except EmployeeNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expended", "-e", help="Expand info about employees")
    ] = False,
) -> None:
    """Show info about employees"""
    env_path = get_env_path(ctx)
    employee_repo = SQLiteEmployeeRepo(env_path)
    handler = EmployeeInfoHandler(employee_repo)
    employees = handler.handle()

    table = Table(title="employees")
    table.add_column("", min_width=7)
    table.add_column("name", min_width=20)
    table.add_column("id", min_width=15)
    if expanded:
        table.add_column("state", min_width=15)
        table.add_column("rest start", min_width=20)

    for i, employee in enumerate(employees):
        params = [i + 1, employee.name, employee.employee_id]
        if expanded:
            params.extend([employee._state, employee.rest_start])

        str_params = map(str, params)
        table.add_row(*str_params)

    if table.row_count > 0:
        console.print(table)

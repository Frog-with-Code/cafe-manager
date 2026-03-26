from typing import Annotated

import typer
from rich.table import Table

from .context import get_env_path, init_context
from .styles import print_info, print_success, print_table

from cafe_manager.domain.services import IDGeneratingService

from cafe_manager.application.use_cases.employee_handlers import (
    EmployeeCreateAtmosphere,
    EmployeeFireHandler,
    EmployeeHireHandler,
    EmployeeInfoHandler,
)

from cafe_manager.infrastructure.sqlite.repositories import SQLiteEmployeeRepo

from cafe_manager.common.exceptions import CLIBusinessError, EmployeeNotFoundError


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
        employee_id = handler.handle(name)

        print_success(f"Employee was hired with ID {employee_id}")
    except RuntimeError as e:
        raise CLIBusinessError(str(e))


@app.command()
def fire(
    ctx: typer.Context,
    employee_id: Annotated[
        str,
        typer.Option("--id", help="ID of the employee"),
    ],
):
    """Fire employee by his ID"""
    env_path = get_env_path(ctx)
    employee_repo = SQLiteEmployeeRepo(env_path)
    handler = EmployeeFireHandler(employee_repo)

    try:
        handler.handle(employee_id)

        print_success(f"Employee was fired")
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
        print_table(table)


@app.command("create-atmosphere")
def create_atmosphere(
    ctx: typer.Context,
):
    """The employee creates the atmosphere by telling a joke"""
    env_path = get_env_path(ctx)
    employee_repo = SQLiteEmployeeRepo(env_path)
    handler = EmployeeCreateAtmosphere(employee_repo)

    try:
        joke = handler.handle()
        print_info("Employee tells a joke:\n{joke}")
    except EmployeeNotFoundError as e:
        raise CLIBusinessError(str(e))

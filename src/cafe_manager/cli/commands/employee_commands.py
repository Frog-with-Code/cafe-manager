from typing import Annotated

import typer
from rich.table import Table

from ..context import get_uow, init_context
from ..styles import print_info, print_success, print_table

from cafe_manager.application.use_cases.employee_handlers import (
    EmployeeCreateAtmosphere,
    EmployeeFireHandler,
    EmployeeHireHandler,
    EmployeeInfoHandler,
)

from cafe_manager.infrastructure.factory import get_id_generator

from cafe_manager.common.exceptions import (
    CLIBusinessError,
    EmployeeNotFoundError,
    IDGeneratingError,
)

app = typer.Typer(callback=init_context, help="Manage cafe staff, hiring, and firing")


@app.command()
def hire(
    ctx: typer.Context,
    name: Annotated[str, typer.Option("--name", "-n", help="Name of the employee")],
):
    """Hire new employee"""
    uow = get_uow(ctx)
    id_generator = get_id_generator()
    handler = EmployeeHireHandler(uow=uow, id_generator=id_generator)

    try:
        employee_id = handler.handle(name)

        print_success(f"Employee was hired with ID {employee_id}")
    except IDGeneratingError as e:
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
    uow = get_uow(ctx)
    handler = EmployeeFireHandler(uow)

    try:
        handler.handle(employee_id)

        print_success(f"Employee was fired")
    except EmployeeNotFoundError as e:
        raise CLIBusinessError(str(e))


@app.command()
def info(
    ctx: typer.Context,
    expanded: Annotated[
        bool, typer.Option("--expanded", "-e", help="Expand info about employees")
    ] = False,
) -> None:
    """Show info about employees"""
    uow = get_uow(ctx)
    handler = EmployeeInfoHandler(uow)
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
    uow = get_uow(ctx)
    handler = EmployeeCreateAtmosphere(uow)

    try:
        joke = handler.handle()
        print_info(f"Employee tells a joke:\n{joke}")
    except EmployeeNotFoundError as e:
        raise CLIBusinessError(str(e))

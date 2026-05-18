import typer
import sys

from .commands import *

from cafe_manager.common.exceptions import CLIBusinessError, CLIUnexpectedError


app = typer.Typer(pretty_exceptions_enable=True)

app.add_typer(order_app, name="order")
app.add_typer(employee_app, name="employee")
app.add_typer(inventory_app, name="inventory")
app.add_typer(kitchen_app, name="kitchen")
app.add_typer(menu_app, name="menu")
app.add_typer(table_app, name="table")
app.add_typer(chair_app, name="chair")
app.add_typer(machine_app, name="machine")
app.add_typer(cafe_app, name="cafe")
app.add_typer(finance_app, name="finance")
app.add_typer(client_app, name="client")


def run_app():
    try:
        app()
    except CLIBusinessError:
        raise
    except Exception as e:
        cli_e = CLIUnexpectedError(str(e))
        cli_e.show()
        sys.exit(cli_e.exit_code)


if __name__ == "__main__":
    run_app()

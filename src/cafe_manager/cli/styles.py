from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def print_success(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    err_console.print(f"[red]{message}[/red]")


def print_info(message: str) -> None:
    console.print(f"[white]{message}[/white]")


def print_warning(message: str) -> None:
    err_console.print(f"[yellow]{message}[/yellow]")


def print_info_important(message: str) -> None:
    console.print(f"[magenta]{message}[/magenta]")


def print_table(table: Table) -> None:
    console.print(table)

from typing import Any

from nicegui import ui

from .state import refreshers
from .tabs import (
    cafe,
    chairs,
    clients,
    employees,
    finance,
    inventory,
    kitchen,
    machines,
    menu,
    orders,
    tables,
)


@ui.page("/ui")
def main_page() -> None:
    ui.page_title("Cafma")

    with ui.header().classes("bg-brown-800 text-white"):
        ui.label("☕ Cafma").classes("text-2xl font-bold font-serif p-2")

    with ui.tabs().classes("w-full") as tabs:
        t_cafe = ui.tab("Cafe")
        t_orders = ui.tab("Orders")
        t_kitchen = ui.tab("Kitchen")
        t_tables = ui.tab("Tables")
        t_chairs = ui.tab("Chairs")
        t_employees = ui.tab("Employees")
        t_menu = ui.tab("Menu")
        t_inventory = ui.tab("Inventory")
        t_finance = ui.tab("Finance")
        t_clients = ui.tab("Clients")
        t_machines = ui.tab("Machines")

    with ui.tab_panels(tabs, value=t_cafe).classes("w-full") as panels:
        with ui.tab_panel(t_cafe):
            cafe.tab_cafe()
        with ui.tab_panel(t_orders):
            orders.tab_orders()
        with ui.tab_panel(t_kitchen):
            kitchen.tab_kitchen()
        with ui.tab_panel(t_tables):
            tables.tab_tables()
        with ui.tab_panel(t_chairs):
            chairs.tab_chairs()
        with ui.tab_panel(t_employees):
            employees.tab_employees()
        with ui.tab_panel(t_menu):
            menu.tab_menu()
        with ui.tab_panel(t_inventory):
            inventory.tab_inventory()
        with ui.tab_panel(t_finance):
            finance.tab_finance()
        with ui.tab_panel(t_clients):
            clients.tab_clients()
        with ui.tab_panel(t_machines):
            machines.tab_machines()

    async def on_tab_change(e: Any) -> None:
        tab_name: str = e.args if isinstance(e.args, str) else str(e.args)
        print(f"Tab changed to: {tab_name!r}")
        refresh = refreshers.get(tab_name)
        if refresh:
            await refresh()

    tabs.on("update:modelValue", on_tab_change)


def run_ui() -> None:
    ui.run(title="Cafma", port=8080, reload=False)


if __name__ == "__main__":
    run_ui()

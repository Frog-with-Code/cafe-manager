from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    confirm_delete,
    expansion,
    notify_result,
    num,
    required_inp,
    safe_rows,
    validate_fields,
)
from ..http_helpers import api_delete, api_get, api_post
from ..state import refreshers


def tab_inventory() -> None:
    with ui.card().classes("w-full"):
        ui.label("Inventory").classes("text-lg font-bold")
        inv_table = ui.table(
            columns=[
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "unit", "label": "Unit", "field": "unit"},
                {"name": "amount", "label": "Amount", "field": "amount"},
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_inventory() -> None:
            data, err = await api_get("/inventory/")
            if err:
                ui.notify(err, type="negative")
            else:
                inv_table.rows = safe_rows(data)
                inv_table.update()

        refreshers["Inventory"] = refresh_inventory

        ui.timer(0, refresh_inventory, once=True)
        ui.button("Refresh", on_click=refresh_inventory)

        with expansion("Add ingredient"):
            ing_name = required_inp("Name", min_len=2)
            ing_unit = ui.select(["g", "ml"], label="Unit", value="g").classes("w-24")

            async def add_ingredient() -> None:
                if not validate_fields(ing_name):
                    return
                data, err = await api_post(
                    "/inventory/",
                    params={"name": ing_name.value, "unit": ing_unit.value},
                )
                notify_result(data, err)
                await refresh_inventory()

            ui.button("Add", on_click=add_ingredient)

        with expansion("Restock ingredient"):
            sup_name = required_inp("Ingredient name", min_len=2)
            sup_qty = num("Quantity", value=1.0, min=0.01)
            sup_price = num("Cost", value=0.0, min=0)

            async def supply_inventory() -> None:
                if not validate_fields(sup_name):
                    return
                data, err = await api_post(
                    "/inventory/supply",
                    params={
                        "name": sup_name.value,
                        "quantity": sup_qty.value or 1.0,
                        "price": sup_price.value or 0.0,
                    },
                )
                notify_result(data, err)
                await refresh_inventory()

            ui.button("Restock", on_click=supply_inventory)

        with expansion("Remove ingredient"):
            del_ing = required_inp("Ingredient name", min_len=2)

            async def _do_remove_ingredient() -> None:
                data, err = await api_delete(f"/inventory/{del_ing.value}")
                notify_result(data, err)
                await refresh_inventory()

            async def remove_ingredient() -> None:
                if not validate_fields(del_ing):
                    return
                await confirm_delete(
                    f'Remove ingredient "{del_ing.value}"?', _do_remove_ingredient
                )

            ui.button("Remove", color="red", on_click=remove_ingredient)

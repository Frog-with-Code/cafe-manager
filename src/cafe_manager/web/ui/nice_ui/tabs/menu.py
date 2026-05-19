from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    area,
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


def tab_menu() -> None:
    with ui.card().classes("w-full"):
        ui.label("Menu").classes("text-lg font-bold")

        menu_container = ui.column().classes("w-full")

        async def refresh_menu() -> None:
            menu_container.clear()
            data, err = await api_get("/menu/")
            if err:
                ui.notify(err, type="negative")
                return
            if not isinstance(data, dict):
                return
            with menu_container:
                for category, items in data.items():
                    ui.label(category).classes("font-bold mt-2")
                    rows = [
                        {
                            "name": i["name"],
                            "price": i["price"],
                            "category": i["category"],
                        }
                        for i in items
                        if isinstance(i, dict)
                    ]
                    ui.table(
                        columns=[
                            {"name": "name", "label": "Name", "field": "name"},
                            {"name": "price", "label": "Price", "field": "price"},
                            {
                                "name": "category",
                                "label": "Category",
                                "field": "category",
                            },
                        ],
                        rows=rows,
                        pagination=PAGE_SIZE,
                    ).classes("w-full")

        refreshers["Menu"] = refresh_menu

        ui.timer(0, refresh_menu, once=True)
        ui.button("Refresh", on_click=refresh_menu)

        with expansion("Add menu item"):
            m_name = required_inp("Name", min_len=2)
            m_price = num("Price", value=0.0, min=0)
            m_category = ui.select(
                ["coffee", "tea", "cocktail", "smoothie", "bakery", "soup"],
                label="Category",
                value="coffee",
            ).classes("w-48")
            ui.markdown("**Ingredients format:** `name:amount`, one per line")
            m_ingr = area("Ingredients")

            async def add_menu_item() -> None:
                if not validate_fields(m_name):
                    return
                ingr_dict: dict[str, float] = {}
                for line in (m_ingr.value or "").strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        ingr_dict[k.strip()] = float(v.strip())
                data, err = await api_post(
                    "/menu/",
                    params={
                        "name": m_name.value,
                        "price": m_price.value or 0.0,
                        "category": m_category.value,
                    },
                    json=ingr_dict,
                )
                notify_result(data, err)
                await refresh_menu()

            ui.button("Add", on_click=add_menu_item)

        with expansion("View item ingredients"):
            ingr_item_name = required_inp("Item name", min_len=2)
            ingr_table = ui.table(
                columns=[
                    {"name": "name", "label": "Ingredient", "field": "name"},
                    {"name": "amount", "label": "Amount", "field": "amount"},
                    {"name": "unit", "label": "Unit", "field": "unit"},
                ],
                rows=[],
                pagination=PAGE_SIZE,
            ).classes("w-full")

            async def load_ingredients() -> None:
                if not ingr_item_name.validate():
                    return
                data, err = await api_get(f"/menu/{ingr_item_name.value}/ingredients")
                if err:
                    ui.notify(err, type="negative")
                else:
                    ingr_table.rows = safe_rows(data)
                    ingr_table.update()

            ui.button("Show ingredients", on_click=load_ingredients)

        with expansion("Remove menu item"):
            del_item = required_inp("Item name", min_len=2)

            async def _do_remove_item() -> None:
                data, err = await api_delete(f"/menu/{del_item.value}")
                notify_result(data, err)
                await refresh_menu()

            async def remove_menu_item() -> None:
                if not validate_fields(del_item):
                    return
                await confirm_delete(
                    f'Remove menu item "{del_item.value}"?', _do_remove_item
                )

            ui.button("Remove", color="red", on_click=remove_menu_item)

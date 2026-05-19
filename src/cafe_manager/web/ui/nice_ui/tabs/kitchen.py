from typing import Any

from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    expansion,
    inp,
    notify_result,
    required_inp,
    safe_rows,
    validate_fields,
)
from ..http_helpers import api_get, api_post
from ..state import refreshers


def tab_kitchen() -> None:
    with ui.card().classes("w-full"):
        ui.label("Kitchen").classes("text-lg font-bold")
        kitchen_table = ui.table(
            columns=[
                {"name": "id", "label": "Order ID", "field": "id"},
                {"name": "state", "label": "State", "field": "state"},
                {"name": "table_id", "label": "Table", "field": "table_id"},
                {"name": "total_price", "label": "Total", "field": "total_price"},
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_kitchen() -> None:
            data, err = await api_get("/kitchen/pending")
            if err:
                ui.notify(err, type="negative")
            else:
                kitchen_table.rows = safe_rows(data)
                kitchen_table.update()

        refreshers["Kitchen"] = refresh_kitchen

        ui.timer(0, refresh_kitchen, once=True)
        ui.button("Refresh", on_click=refresh_kitchen)

        with expansion("Start cooking next order"):
            cook_emp = inp("Employee ID (optional)")

            async def start_cooking() -> None:
                params: dict[str, Any] = {}
                if cook_emp.value:
                    params["employee_id"] = cook_emp.value
                data, err = await api_post("/kitchen/start", params=params)
                notify_result(data, err)
                await refresh_kitchen()

            ui.button("Start", on_click=start_cooking)

        with expansion("Mark order as ready"):
            ready_order = required_inp("Order ID")

            async def mark_ready() -> None:
                if not validate_fields(ready_order):
                    return
                data, err = await api_post(f"/kitchen/{ready_order.value}/complete")
                notify_result(data, err)
                await refresh_kitchen()

            ui.button("Mark ready", on_click=mark_ready)

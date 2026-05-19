from typing import Any

from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    confirm_delete,
    expansion,
    inp,
    notify_result,
    num,
    safe_int,
    safe_rows,
)
from ..http_helpers import api_delete, api_get, api_post
from ..state import refreshers


def tab_chairs() -> None:
    with ui.card().classes("w-full"):
        ui.label("Chairs").classes("text-lg font-bold")
        chair_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "state", "label": "State", "field": "state"},
                {"name": "table_id", "label": "Table", "field": "table_id"},
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_chairs() -> None:
            data, err = await api_get("/chair/info")
            if err:
                ui.notify(err, type="negative")
            else:
                chair_table.rows = safe_rows(data)
                chair_table.update()

        refreshers["Chairs"] = refresh_chairs

        ui.timer(0, refresh_chairs, once=True)
        ui.button("Refresh", on_click=refresh_chairs)

        with expansion("Buy chair"):
            chair_price = num("Price", value=0.0, min=0)
            chair_account = inp("Account ID (optional)")

            async def buy_chair() -> None:
                params: dict[str, Any] = {"price": chair_price.value or 0.0}
                if chair_account.value:
                    params["account_id"] = chair_account.value
                data, err = await api_post("/chair/buy", params=params)
                notify_result(data, err)
                await refresh_chairs()

            ui.button("Buy", on_click=buy_chair)

        with expansion("Discard chair"):
            discard_chair_id = num("Chair ID", value=1, min=1)

            async def _do_discard_chair() -> None:
                data, err = await api_delete(
                    "/chair/discard",
                    params={"chair_id": safe_int(discard_chair_id.value)},
                )
                notify_result(data, err)
                await refresh_chairs()

            async def discard_chair() -> None:
                await confirm_delete(
                    f"Discard chair #{safe_int(discard_chair_id.value)}?",
                    _do_discard_chair,
                )

            ui.button("Discard", color="red", on_click=discard_chair)

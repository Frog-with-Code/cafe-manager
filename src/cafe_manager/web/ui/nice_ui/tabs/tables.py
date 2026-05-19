from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    confirm_delete,
    expansion,
    notify_result,
    num,
    safe_int,
    safe_rows,
)
from ..http_helpers import api_delete, api_get, api_post
from ..state import refreshers


def tab_tables() -> None:
    with ui.card().classes("w-full"):
        ui.label("Tables").classes("text-lg font-bold")
        table_tbl = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "capacity", "label": "Capacity", "field": "capacity"},
                {"name": "state", "label": "State", "field": "state"},
                {"name": "chairs", "label": "Chairs", "field": "chairs"},
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_tables() -> None:
            data, err = await api_get("/table/")
            if err:
                ui.notify(err, type="negative")
            else:
                rows = safe_rows(data)
                for row in rows:
                    if isinstance(row.get("chairs"), list):
                        row["chairs"] = ", ".join(str(c) for c in row["chairs"])
                table_tbl.rows = rows
                table_tbl.update()

        refreshers["Tables"] = refresh_tables

        ui.timer(0, refresh_tables, once=True)
        ui.button("Refresh", on_click=refresh_tables)

        with expansion("Buy table"):
            tbl_price = num("Price", value=0.0, min=0)
            tbl_seats = num("Seats", value=4, min=1)

            async def buy_table() -> None:
                data, err = await api_post(
                    "/table/",
                    params={
                        "price": tbl_price.value or 0.0,
                        "seats": safe_int(tbl_seats.value, 4),
                    },
                )
                notify_result(data, err)
                await refresh_tables()

            ui.button("Buy", on_click=buy_table)

        with expansion("Reserve table"):
            res_seats = num("Seats required", value=2, min=1)

            async def reserve_table() -> None:
                data, err = await api_post(
                    "/table/reserve",
                    params={"seats_required": safe_int(res_seats.value, 2)},
                )
                notify_result(data, err)
                await refresh_tables()

            ui.button("Reserve", on_click=reserve_table)

        with expansion("Free table"):
            free_id = num("Table ID", value=1, min=1)

            async def free_table() -> None:
                data, err = await api_post(f"/table/{safe_int(free_id.value)}/free")
                notify_result(data, err)
                await refresh_tables()

            ui.button("Free", on_click=free_table)

        with expansion("Discard table"):
            del_tbl = num("Table ID", value=1, min=1)

            async def _do_discard_table() -> None:
                data, err = await api_delete(f"/table/{safe_int(del_tbl.value)}")
                notify_result(data, err)
                await refresh_tables()

            async def discard_table() -> None:
                await confirm_delete(
                    f"Discard table #{safe_int(del_tbl.value)}?", _do_discard_table
                )

            ui.button("Discard", color="red", on_click=discard_table)

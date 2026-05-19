from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    expansion,
    notify_result,
    required_inp,
    safe_rows,
    validate_fields,
)
from ..http_helpers import api_get, api_post
from ..state import refreshers


def tab_clients() -> None:
    with ui.card().classes("w-full"):
        ui.label("Clients").classes("text-lg font-bold")
        client_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "total_spent", "label": "Total spent", "field": "total_spent"},
                {"name": "orders_amount", "label": "Orders", "field": "orders_amount"},
                {
                    "name": "registered_at",
                    "label": "Registered",
                    "field": "registered_at",
                },
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_clients() -> None:
            data, err = await api_get("/client/")
            if err:
                ui.notify(err, type="negative")
            else:
                client_table.rows = safe_rows(data)
                client_table.update()

        refreshers["Clients"] = refresh_clients

        ui.timer(0, refresh_clients, once=True)
        ui.button("Refresh", on_click=refresh_clients)

        with expansion("Register client"):
            new_client_name = required_inp("Client name", min_len=2)

            async def create_client() -> None:
                if not validate_fields(new_client_name):
                    return
                data, err = await api_post(
                    "/client/", params={"name": new_client_name.value}
                )
                notify_result(data, err)

            ui.button("Register", on_click=create_client)

        with expansion("View client by ID"):
            client_id_input = required_inp("Client ID")
            client_info_label = ui.label("").classes("italic text-gray-600")

            async def get_client() -> None:
                if not validate_fields(client_id_input):
                    return
                data, err = await api_get(f"/client/{client_id_input.value}")
                if err:
                    ui.notify(err, type="negative")
                elif isinstance(data, dict):
                    client_info_label.set_text(
                        f"{data.get('name', '—')} | Spent: {data.get('total_spent', '—')} | Orders: {data.get('orders_amount', '—')}"
                    )

            ui.button("Show", on_click=get_client)

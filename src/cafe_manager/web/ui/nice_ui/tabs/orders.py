from typing import Any

from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    area,
    expansion,
    inp,
    notify_result,
    num,
    required_inp,
    safe_int,
    safe_rows,
    validate_fields,
)
from ..http_helpers import api_get, api_post
from ..state import refreshers


def tab_orders() -> None:
    with ui.card().classes("w-full"):
        ui.label("Active Orders").classes("text-lg font-bold")
        order_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "state", "label": "State", "field": "state"},
                {"name": "table_id", "label": "Table", "field": "table_id"},
                {"name": "total_price", "label": "Total", "field": "total_price"},
                {"name": "created_at", "label": "Created", "field": "created_at"},
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_orders() -> None:
            data, err = await api_get("/order/active")
            if err:
                ui.notify(err, type="negative")
            else:
                order_table.rows = safe_rows(data)
                order_table.update()

        refreshers["Orders"] = refresh_orders

        ui.timer(0, refresh_orders, once=True)
        ui.button("Refresh", on_click=refresh_orders)

        with expansion("Create order"):
            ui.markdown("**Items format:** `name:quantity`, one per line")
            items_text = area("Items (name:qty)")
            order_table_id = num("Table ID (optional)", value=None)
            continue_session = ui.checkbox("Add to existing table session")

            async def create_order() -> None:
                items: dict[str, int] = {}
                for line in (items_text.value or "").strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        name = k.strip()
                        qty = int(v.strip())
                        items[name] = items.get(name, 0) + qty
                if not items:
                    ui.notify("Add at least one item", type="warning")
                    return
                params: dict[str, Any] = {"continue_session": continue_session.value}
                if order_table_id.value is not None:
                    params["table_id"] = safe_int(order_table_id.value)
                data, err = await api_post("/order/", params=params, json=items)
                notify_result(data, err)
                await refresh_orders()

            ui.button("Create", on_click=create_order)

    with expansion("Pay order"):
        pay_order_id = required_inp("Order ID")
        pay_amount = num("Amount", value=0.0, min=0)
        pay_client_id = inp("Client ID (optional)")

        async def pay_order() -> None:
            if not validate_fields(pay_order_id):
                return
            params: dict[str, Any] = {"amount_provided": pay_amount.value or 0.0}
            if pay_client_id.value:
                params["client_id"] = pay_client_id.value
            data, err = await api_post(
                f"/order/{pay_order_id.value}/pay",
                params=params,
            )
            notify_result(data, err)
            await refresh_orders()

        ui.button("Pay", on_click=pay_order)

        with expansion("View order items"):
            order_items_id = required_inp("Order ID")
            order_items_table = ui.table(
                columns=[
                    {"name": "name", "label": "Item", "field": "name"},
                    {"name": "qty", "label": "Quantity", "field": "qty"},
                ],
                rows=[],
                pagination=PAGE_SIZE,
            ).classes("w-full")

            async def load_order_items() -> None:
                if not order_items_id.validate():
                    return
                data, err = await api_get(f"/order/{order_items_id.value}/items")
                if err:
                    ui.notify(err, type="negative")
                elif isinstance(data, dict):
                    items = data.get("items", {})
                    if isinstance(items, dict):
                        order_items_table.rows = [
                            {"name": name, "qty": qty} for name, qty in items.items()
                        ]
                        order_items_table.update()

            ui.button("Show items", on_click=load_order_items)

        with expansion("Mark order as served"):
            serve_id = required_inp("Order ID")

            async def serve_order() -> None:
                if not validate_fields(serve_id):
                    return
                data, err = await api_post(f"/order/{serve_id.value}/serve")
                notify_result(data, err)
                await refresh_orders()

            ui.button("Serve", on_click=serve_order)

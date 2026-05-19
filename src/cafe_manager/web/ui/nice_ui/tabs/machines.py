from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    confirm_delete,
    expansion,
    notify_result,
    num,
    required_inp,
    safe_int,
    safe_rows,
    validate_fields,
)
from ..http_helpers import api_delete, api_get, api_post
from ..state import refreshers


def tab_machines() -> None:
    with ui.card().classes("w-full"):
        ui.label("Coffee Machines").classes("text-lg font-bold")
        mach_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "model", "label": "Model", "field": "model"},
                {"name": "state", "label": "State", "field": "state"},
                {"name": "cycles", "label": "Cycles", "field": "cycles"},
                {"name": "limit", "label": "Limit", "field": "limit"},
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_machines() -> None:
            data, err = await api_get("/machine/")
            if err:
                ui.notify(err, type="negative")
            else:
                mach_table.rows = safe_rows(data)
                mach_table.update()

        refreshers["Machines"] = refresh_machines

        ui.timer(0, refresh_machines, once=True)
        ui.button("Refresh", on_click=refresh_machines)

        with expansion("Buy machine"):
            m_price = num("Price", value=0.0, min=0)
            m_model = required_inp("Model", min_len=2)
            m_limit = num("Cycle limit", value=1000, min=1)

            async def buy_machine() -> None:
                if not validate_fields(m_model):
                    return
                data, err = await api_post(
                    "/machine/",
                    params={
                        "price": m_price.value or 0.0,
                        "model": m_model.value,
                        "limit": safe_int(m_limit.value, 1000),
                    },
                )
                notify_result(data, err)
                await refresh_machines()

            ui.button("Buy", on_click=buy_machine)

        with expansion("Manage machine state"):
            m_id = num("Machine ID", value=1, min=1)

            async def service_machine() -> None:
                data, err = await api_post(f"/machine/{safe_int(m_id.value)}/service")
                notify_result(data, err)
                await refresh_machines()

            async def resume_machine() -> None:
                data, err = await api_post(f"/machine/{safe_int(m_id.value)}/resume")
                notify_result(data, err)
                await refresh_machines()

            async def _do_discard_machine() -> None:
                data, err = await api_delete(f"/machine/{safe_int(m_id.value)}")
                notify_result(data, err)
                await refresh_machines()

            async def discard_machine() -> None:
                await confirm_delete(
                    f"Discard machine #{safe_int(m_id.value)}?", _do_discard_machine
                )

            with ui.row():
                ui.button("Send to service", color="orange", on_click=service_machine)
                ui.button("Return from service", on_click=resume_machine)
                ui.button("Discard", color="red", on_click=discard_machine)

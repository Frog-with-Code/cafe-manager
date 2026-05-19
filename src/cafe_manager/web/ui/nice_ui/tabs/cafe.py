from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    confirm_delete,
    notify_result,
    num,
    required_inp,
    safe_rows,
    expansion,
    validate_fields,
)
from ..http_helpers import api_delete, api_get, api_post
from ..state import refreshers


def tab_cafe() -> None:
    with ui.card().classes("w-full"):
        ui.label("Cafe Environments").classes("text-lg font-bold")

        cafe_table = ui.table(
            columns=[
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "path", "label": "Path", "field": "path"},
                {"name": "is_active", "label": "Active", "field": "is_active"},
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_cafes() -> None:
            data, err = await api_get("/cafe/")
            if err:
                ui.notify(err, type="negative")
            else:
                cafe_table.rows = safe_rows(data)
                cafe_table.update()

        refreshers["Cafe"] = refresh_cafes

        ui.timer(0, refresh_cafes, once=True)
        ui.button("Refresh", on_click=refresh_cafes)

        with expansion("Create environment"):
            new_name = required_inp("Cafe name", min_len=2)

            async def create_cafe() -> None:
                if not validate_fields(new_name):
                    return
                data, err = await api_post("/cafe/", params={"name": new_name.value})
                notify_result(data, err)
                await refresh_cafes()

            ui.button("Create", on_click=create_cafe)

        with expansion("Activate / Deactivate"):
            act_name = required_inp("Environment name", min_len=2)

            async def activate_cafe() -> None:
                if not validate_fields(act_name):
                    return
                data, err = await api_post(f"/cafe/activate/{act_name.value}")
                notify_result(data, err)
                await refresh_cafes()

            async def deactivate_cafe() -> None:
                data, err = await api_post("/cafe/deactivate")
                notify_result(data, err)
                await refresh_cafes()

            with ui.row():
                ui.button("Activate", on_click=activate_cafe)
                ui.button("Deactivate", color="orange", on_click=deactivate_cafe)

        with expansion("Initialize active environment"):
            init_name = required_inp("Name", min_len=2)
            init_addr = required_inp("Address", min_len=5)
            init_capital = num("Starting capital", value=0.0, min=0)

            async def init_cafe() -> None:
                if not validate_fields(init_name, init_addr):
                    return
                data, err = await api_post(
                    "/cafe/init",
                    params={
                        "name": init_name.value,
                        "address": init_addr.value,
                        "capital": init_capital.value or 0.0,
                    },
                )
                notify_result(data, err)

            ui.button("Initialize", on_click=init_cafe)

        with expansion("Delete environment"):
            del_name = required_inp("Environment name", min_len=2)

            async def _do_delete_cafe() -> None:
                data, err = await api_delete(f"/cafe/{del_name.value}")
                notify_result(data, err)
                await refresh_cafes()

            async def delete_cafe() -> None:
                if not validate_fields(del_name):
                    return
                await confirm_delete(
                    f'Delete environment "{del_name.value}"?', _do_delete_cafe
                )

            ui.button("Delete", color="red", on_click=delete_cafe)

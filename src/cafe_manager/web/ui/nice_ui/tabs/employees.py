from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    confirm_delete,
    expansion,
    notify_result,
    required_inp,
    safe_rows,
    validate_fields,
)
from ..http_helpers import api_delete, api_get, api_post
from ..state import refreshers


def tab_employees() -> None:
    with ui.card().classes("w-full"):
        ui.label("Employees").classes("text-lg font-bold")
        emp_table = ui.table(
            columns=[
                {"name": "id", "label": "ID", "field": "id"},
                {"name": "name", "label": "Name", "field": "name"},
                {"name": "state", "label": "State", "field": "state"},
                {
                    "name": "rest_start",
                    "label": "On break since",
                    "field": "rest_start",
                },
            ],
            rows=[],
            pagination=PAGE_SIZE,
        ).classes("w-full")

        async def refresh_employees() -> None:
            data, err = await api_get("/employee/")
            if err:
                ui.notify(err, type="negative")
            else:
                emp_table.rows = safe_rows(data)
                emp_table.update()

        refreshers["Employees"] = refresh_employees

        ui.timer(0, refresh_employees, once=True)
        ui.button("Refresh", on_click=refresh_employees)

        with expansion("Hire employee"):
            emp_name = required_inp("Employee name", min_len=2)

            async def hire_employee() -> None:
                if not validate_fields(emp_name):
                    return
                data, err = await api_post(
                    "/employee/", params={"name": emp_name.value}
                )
                notify_result(data, err)
                await refresh_employees()

            ui.button("Hire", on_click=hire_employee)

        with expansion("Fire employee"):
            fire_id = required_inp("Employee ID")

            async def _do_fire() -> None:
                data, err = await api_delete(f"/employee/{fire_id.value}")
                notify_result(data, err)
                await refresh_employees()

            async def fire_employee() -> None:
                if not validate_fields(fire_id):
                    return
                await confirm_delete(f'Fire employee "{fire_id.value}"?', _do_fire)

            ui.button("Fire", color="red", on_click=fire_employee)

        with expansion("Create atmosphere"):
            joke_label = ui.label("").classes("italic text-gray-600")

            async def get_joke() -> None:
                data, err = await api_get("/employee/atmosphere")
                if err:
                    ui.notify(err, type="negative")
                elif isinstance(data, dict):
                    joke_label.set_text(data.get("joke", ""))

            ui.button("Get joke", on_click=get_joke)

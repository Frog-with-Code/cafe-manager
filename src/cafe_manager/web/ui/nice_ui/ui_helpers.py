from typing import Any, Callable, Coroutine
from nicegui import ui

PAGE_SIZE = 10


def notify_result(data: Any, err: str | None) -> None:
    if err:
        ui.notify(f"Error: {err}", type="negative")
    elif isinstance(data, dict):
        msg = data.get("message") or data.get("status") or str(data)
        ui.notify(msg, type="positive")
    else:
        ui.notify("Done", type="positive")


def safe_rows(data: Any) -> list[dict]:
    return data if isinstance(data, list) else []


def safe_int(value: float | None, default: int = 1) -> int:
    return int(value) if value is not None else default


def inp(label: str, **kwargs: Any) -> ui.input:
    """Short text input sized to label."""
    return ui.input(label, **kwargs).classes("w-48")


def num(label: str, **kwargs: Any) -> ui.number:
    """Short number input sized to label."""
    return ui.number(label, **kwargs).classes("w-36")


def area(label: str, **kwargs: Any) -> ui.textarea:
    """Textarea sized moderately."""
    return ui.textarea(label, **kwargs).classes("w-72")


def expansion(title: str) -> ui.expansion:
    """Expansion panel sized to its content."""
    return ui.expansion(title).classes("w-auto")


def required_inp(label: str, min_len: int = 1, **kwargs: Any) -> ui.input:
    """Text input with required validation."""
    field = ui.input(label, **kwargs).classes("w-48")
    field.validation = {
        f"Required (min {min_len} chars)": lambda v, m=min_len: len((v or "").strip())
        >= m
    }
    return field


def validate_fields(*fields: ui.input) -> bool:
    """Run validation on all fields, return True if all pass."""
    return all(f.validate() for f in fields)


async def confirm_delete(
    message: str, on_confirm: Callable[[], Coroutine[Any, Any, None]]
) -> None:
    """Show a confirmation dialog before a delete action."""
    with ui.dialog() as dialog, ui.card():
        ui.label("Confirm deletion").classes("text-lg font-bold text-red-600")
        ui.label(message)
        with ui.row():

            async def do_delete() -> None:
                dialog.close()
                await on_confirm()

            ui.button("Delete", color="red", on_click=do_delete)
            ui.button("Cancel", on_click=dialog.close)
    dialog.open()

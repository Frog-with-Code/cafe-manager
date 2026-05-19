from nicegui import ui

from ..ui_helpers import (
    PAGE_SIZE,
    expansion,
    notify_result,
    num,
    required_inp,
    safe_int,
    safe_rows,
    validate_fields,
)
from ..http_helpers import api_get, api_post
from ..state import refreshers


def tab_finance() -> None:
    with ui.card().classes("w-full"):
        ui.label("Finance").classes("text-lg font-bold")

        with ui.card().classes("w-full bg-blue-50"):
            stats_labels = {
                "balance": ui.label("Balance: —"),
                "income": ui.label("Income: —"),
                "expense": ui.label("Expense: —"),
                "profit_abs": ui.label("Profit: —"),
                "is_loss": ui.label("Loss: —"),
            }

        async def refresh_stats() -> None:
            data, err = await api_get("/finance/stats")
            if err:
                ui.notify(err, type="negative")
            elif isinstance(data, dict):
                stats_labels["balance"].set_text(f"Balance: {data.get('balance', '—')}")
                stats_labels["income"].set_text(f"Income: {data.get('income', '—')}")
                stats_labels["expense"].set_text(f"Expense: {data.get('expense', '—')}")
                stats_labels["profit_abs"].set_text(
                    f"Profit: {data.get('profit_abs', '—')}"
                )
                stats_labels["is_loss"].set_text(
                    f"Loss: {'Yes' if data.get('is_loss') else 'No'}"
                )

        refreshers["Finance"] = refresh_stats

        ui.timer(0, refresh_stats, once=True)
        ui.button("Refresh stats", on_click=refresh_stats)

        with expansion("Transaction history"):
            hist_table = ui.table(
                columns=[
                    {"name": "type", "label": "Type", "field": "type"},
                    {"name": "money", "label": "Amount", "field": "money"},
                    {
                        "name": "description",
                        "label": "Description",
                        "field": "description",
                    },
                    {"name": "time", "label": "Time", "field": "time"},
                ],
                rows=[],
                pagination=PAGE_SIZE,
            ).classes("w-full")
            hist_limit = num("Last N records", value=10, min=1)

            async def refresh_history() -> None:
                data, err = await api_get(
                    "/finance/history", params={"limit": safe_int(hist_limit.value, 10)}
                )
                if err:
                    ui.notify(err, type="negative")
                else:
                    hist_table.rows = safe_rows(data)
                    hist_table.update()

            ui.button("Load history", on_click=refresh_history)

        with expansion("Invest"):
            inv_amount = num("Amount", value=0.0, min=0)
            inv_desc = required_inp("Description", value="Investment")

            async def invest() -> None:
                if not validate_fields(inv_desc):
                    return
                data, err = await api_post(
                    "/finance/invest",
                    params={
                        "amount": inv_amount.value or 0.0,
                        "description": inv_desc.value,
                    },
                )
                notify_result(data, err)
                await refresh_stats()

            ui.button("Invest", on_click=invest)

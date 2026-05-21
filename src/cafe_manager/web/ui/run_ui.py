from nicegui import ui
from .nice_ui import ui_app


def run_ui():
    try:
        ui.run(host="127.0.0.1", port=8080, reload=False)
    except KeyboardInterrupt:
        print("\n\033[32mINFO\033[0m:" + " " * 5 + "Cafma UI stopped.")


if __name__ == "__main__":
    run_ui()

from fastapi import FastAPI

from .exception_handler import add_exception_handlers
from .routers import *

import uvicorn

app = FastAPI(title="Cafe Manager API")

app.include_router(order_router, prefix="/order")
app.include_router(employee_router, prefix="/employee")
app.include_router(inventory_router, prefix="/inventory")
app.include_router(kitchen_router, prefix="/kitchen")
app.include_router(menu_router, prefix="/menu")
app.include_router(table_router, prefix="/table")
app.include_router(chair_router, prefix="/chair")
app.include_router(machine_router, prefix="/machine")
app.include_router(cafe_router, prefix="/cafe")
app.include_router(finance_router, prefix="/finance")
app.include_router(client_router, prefix="/client")

add_exception_handlers(app)


def run_web():
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run_web()

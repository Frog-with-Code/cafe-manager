from .chair_commands import app as chair_app
from .employee_commands import app as employee_app
from .inventory_commands import app as inventory_app
from .kitchen_commands import app as kitchen_app
from .machine_commands import app as machine_app
from .menu_commands import app as menu_app
from .order_commands import app as order_app
from .table_commands import app as table_app
from .cafe_commands import app as cafe_app
from .finance_commands import app as finance_app
from .client_commands import app as client_app

__all__ = [
    "chair_app",
    "employee_app",
    "inventory_app",
    "kitchen_app",
    "machine_app",
    "menu_app",
    "order_app",
    "table_app",
    "cafe_app",
    "finance_app",
    "client_app"
]

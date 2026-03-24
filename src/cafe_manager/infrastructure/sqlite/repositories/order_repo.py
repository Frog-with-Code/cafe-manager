from cafe_manager.infrastructure.interfaces import OrderRepo
from .abstract_repo import *
from cafe_manager.domain.entities.order import *
from cafe_manager.domain.entities.menu import (
    Recipe,
    MenuItem,
    MenuItemCategory,
)


class SQLiteOrderRepo(AbstractSQliteRepo, OrderRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    items TEXT,  
                    table_id INTEGER,
                    client_id TEXT,
                    employee_id TEXT,
                    machine_id INTEGER,   
                    created_at DATETIME, 
                    paid_at TEXT,
                    total_price MONEY, 
                    state TEXT   
                )
                """
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> Order:
        items_dict = self._deserialize_items(row["items"])

        return Order(
            order_id=row["id"],
            items=items_dict,
            table_id=row["table_id"],
            employee_id=row["employee_id"],
            machine_id=row["machine_id"],
            client_id=row["client_id"],
            created_at=row["created_at"],
            paid_at=row["paid_at"],
            total_price=row["total_price"],
            state=OrderState(row["state"]),
        )

    def _serialize_items(self, items: dict[MenuItem, int]) -> str:
        data = []
        for item, amount in items.items():
            data.append(
                {
                    "name": str(item.name),
                    "ingredients": adapt_ingredients_dict(item.recipe.ingredients),
                    "price": str(item.price.amount),
                    "category": str(item.category),
                    "amount": amount,
                }
            )
        return json.dumps(data)

    def _deserialize_items(self, json_string: str) -> dict[MenuItem, int]:
        if not json_string:
            return {}

        data = json.loads(json_string)
        items = {}
        for d in data:
            i = MenuItem(
                name=d["name"],
                recipe=Recipe(
                    convert_ingredients_dict(d["ingredients"]),
                ),
                price=Money.from_any(d["price"]),
                category=MenuItemCategory(d["category"]),
            )
            items[i] = int(d["amount"])

        return items

    def get_by_id(self, order_id: str) -> Order | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from orders WHERE id = ?", (order_id,)
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def get_oldest_paid(self) -> Order | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from orders WHERE state = 'paid' ORDER BY paid_at ASC"
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def get_paid_from_oldest(self) -> list[Order] | None:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * from orders WHERE state = 'paid' ORDER BY paid_at ASC"
            ).fetchall()

            if not rows:
                return None

            orders = [self._convert_to_entity(row) for row in rows]
            return orders

    def save(self, order: Order) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                    INSERT INTO orders (id, items, table_id, client_id, employee_id, machine_id, created_at, paid_at, total_price, state) 
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
                    ON CONFLICT(id) DO UPDATE SET
                    items = excluded.items,  
                    table_id = excluded.table_id,
                    client_id = excluded.client_id,
                    employee_id = excluded.employee_id,
                    machine_id = excluded.machine_id,
                    paid_at = excluded.paid_at,    
                    total_price = excluded.total_price, 
                    state = excluded.state
                """,
                (
                    order.order_id,
                    self._serialize_items(order.items),
                    order.table_id,
                    order.client_id,
                    order.employee_id,
                    order.machine_id,
                    order.created_at,
                    order.paid_at,
                    order.total_price,
                    str(order._state),
                ),
            )
            conn.commit()

    def get_active_by_table_id(self, table_id: int) -> list[Order] | None:
        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * from orders WHERE table_id = ? AND state != 'completed'",
                (table_id,),
            ).fetchall()

            if not rows:
                return None

            orders = [self._convert_to_entity(row) for row in rows]
            return orders

    def get_all_active(self) -> list[Order] | None:
        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * from orders WHERE state != 'completed'"
            ).fetchall()

            if not rows:
                return None

            orders = [self._convert_to_entity(row) for row in rows]
            return orders

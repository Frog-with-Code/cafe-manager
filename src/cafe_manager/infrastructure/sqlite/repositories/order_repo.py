from cafe_manager.infrastructure.interfaces import OrderRepo
from .abstract_repo import *
from cafe_manager.domain.entities.order import *
from cafe_manager.domain.entities.menu import (
    Recipe,
    Ingredient,
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
                    client_id TEXT,
                    table_id INTEGER,
                    items TEXT,     
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
            client_id=row["client_id"],
            table_id=row["table_id"],
            items=items_dict,
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
                    "requires_milk_foam": str(item.recipe.requires_milk_foam),
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
                    d["requires_milk_foam"] == "True",
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
                    INSERT INTO orders (id, client_id, table_id, items, created_at, paid_at, total_price, state) 
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?) 
                    ON CONFLICT(id) DO UPDATE SET
                    client_id = excluded.client_id,
                    table_id = excluded.table_id,
                    items = excluded.items,       
                    paid_at = excluded.paid_at,    
                    total_price = excluded.total_price, 
                    state = excluded.state
                """,
                (
                    order.order_id,
                    order.client_id,
                    order.table_id,
                    self._serialize_items(order.items),
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

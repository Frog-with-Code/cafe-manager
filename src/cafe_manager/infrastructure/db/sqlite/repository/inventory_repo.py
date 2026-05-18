from cafe_manager.application.uow import InventoryRepo
from .abstract_repo import *
from cafe_manager.domain.entities.menu import Ingredient, Unit


class SQLiteInventoryRepo(AbstractSQliteRepo, InventoryRepo):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection)

    def _init_db(self) -> None:
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS inventory (
                name TEXT PRIMARY KEY,
                unit TEXT,
                amount REAL,
                reserved REAL
                )"""
        )

    def _convert_to_entity(self, row: sqlite3.Row) -> tuple[Ingredient, float]:
        return Ingredient(row["name"], Unit(row["unit"])), row["amount"]

    def get_by_names(self, names: set[str]) -> dict[Ingredient, float] | None:
        placeholders = ", ".join(["?"] * len(names))
        rows = self._conn.execute(
            f"SELECT * from inventory WHERE name IN ({placeholders})", tuple(names)
        ).fetchall()

        if not rows:
            return None

        inventory = dict(self._convert_to_entity(row) for row in rows)
        return inventory

    def save_many(self, inventory: dict[Ingredient, float]) -> None:
        params = [
            (ingredient.name, str(ingredient.unit), amount)
            for ingredient, amount in inventory.items()
        ]
        self._conn.executemany(
            """
                INSERT INTO inventory (name, unit, amount, reserved) 
                VALUES(?, ?, ?, 0) 
                ON CONFLICT(name) DO UPDATE SET
                amount = excluded.amount,
                unit = excluded.unit
            """,
            params,
        )

    def delete_by_name(self, name: str) -> None:
        self._conn.execute("DELETE FROM inventory WHERE name = ?", (name,))

    def get_all(self) -> dict[Ingredient, float] | None:
        rows = self._conn.execute(
            f"SELECT * from inventory",
        ).fetchall()

        if not rows:
            return None

        inventory = dict(self._convert_to_entity(row) for row in rows)
        return inventory

    def add_ingredient_by_name(self, name: str, amount: float) -> None:
        self._conn.execute(
            "UPDATE inventory SET amount = amount + ? WHERE name = ?",
            (amount, name),
        )

    def get_free_by_name(self, name: str) -> float | None:
        row = self._conn.execute(
            "SELECT * from inventory WHERE name = ?",
            (name,),
        ).fetchone()

        if not row:
            return None

        return row["amount"] - row["reserved"]

    def reserve(self, ingredients: dict[Ingredient, float]) -> None:
        params = [
            (amount, ingredient.name) for ingredient, amount in ingredients.items()
        ]

        self._conn.executemany(
            """
                UPDATE inventory 
                SET reserved = reserved + ? 
                WHERE name = ?
                """,
            params,
        )

    def withdraw(self, ingredients: dict[Ingredient, float]) -> None:
        params = [
            (amount, amount, ingredient.name)
            for ingredient, amount in ingredients.items()
        ]

        self._conn.executemany(
            """
                UPDATE inventory 
                SET amount = amount - ?,
                    reserved = reserved - ?
                WHERE name = ?
                """,
            params,
        )

from cafe_manager.application.interfaces import InventoryRepo
from .abstract_repo import *
from cafe_manager.domain.entities.menu import Ingredient, Unit


class SQLiteInventoryRepo(AbstractSQliteRepo, InventoryRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS inventory (
                name TEXT PRIMARY KEY,
                unit TEXT,
                amount REAL,
                reserved REAL
                )"""
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> tuple[Ingredient, float]:
        return Ingredient(row["name"], Unit(row["unit"])), row["amount"]

    def get_by_names(self, names: set[str]) -> dict[Ingredient, float] | None:
        with self._get_connection() as conn:
            placeholders = ", ".join(["?"] * len(names))
            rows = conn.execute(
                f"SELECT * from inventory WHERE name IN ({placeholders})", tuple(names)
            ).fetchall()

            if not rows:
                return None

            inventory = dict(self._convert_to_entity(row) for row in rows)
            return inventory

    def save_many(self, inventory: dict[Ingredient, float]) -> None:
        with self._get_connection() as conn:
            params = [
                (ingredient.name, str(ingredient.unit), amount)
                for ingredient, amount in inventory.items()
            ]
            conn.executemany(
                """
                INSERT INTO inventory (name, unit, amount, reserved) 
                VALUES(?, ?, ?, 0) 
                ON CONFLICT(name) DO UPDATE SET
                amount = excluded.amount,
                unit = excluded.unit
            """,
                params,
            )

            conn.commit()

    def delete_by_name(self, name: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM inventory WHERE name = ?", (name,))
            conn.commit()

    def get_all(self) -> dict[Ingredient, float] | None:
        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * from inventory",
            ).fetchall()

            if not rows:
                return None

            inventory = dict(self._convert_to_entity(row) for row in rows)
            return inventory

    def add_ingredient_by_name(self, name: str, amount: float) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE inventory SET amount = amount + ? WHERE name = ?",
                (amount, name),
            )
            conn.commit()

    def get_free_by_name(self, name: str) -> float | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from inventory WHERE name = ?",
                (name),
            ).fetchone()

            if not row:
                return None

            return row["amount"] - row["reserved"]

    def reserve(self, ingredients: dict[Ingredient, float]) -> None:
        params = [
            (amount, ingredient.name) for ingredient, amount in ingredients.items()
        ]

        with self._get_connection() as conn:
            conn.executemany(
                """
                UPDATE inventory 
                SET reserved = reserved + ? 
                WHERE name = ?
                """,
                params,
            )
            conn.commit()

    def withdraw(self, ingredients: dict[Ingredient, float]) -> None:
        params = [
            (amount, amount, ingredient.name)
            for ingredient, amount in ingredients.items()
        ]

        with self._get_connection() as conn:
            conn.executemany(
                """
                UPDATE inventory 
                SET amount = amount - ?,
                    reserved = reserved - ?
                WHERE name = ?
                """,
                params,
            )
            conn.commit()
            

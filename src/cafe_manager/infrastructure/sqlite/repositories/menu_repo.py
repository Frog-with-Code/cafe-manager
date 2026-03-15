from .abstract_repo import *
from cafe_manager.domain.entities.menu import *


class SQLiteMenuRepo(AbstractSQliteRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS menu (
                    name TEXT PRIMARY KEY,
                    requires_milk_foam TEXT,
                    ingredients INGR_DICT,
                    price MONEY,
                    category TEXT
                )"""
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> MenuItem:
        return MenuItem(
            name=row["name"],
            recipe=Recipe(
                row["requires_milk_foam"] == "True",
                convert_ingredients_dict(row["ingredients"]),
            ),
            price=row["price"],
            category=MenuItemCategory(row["category"]),
        )

    def get_by_names(self, names: set[str]) -> set[MenuItem] | None:
        with self._get_connection() as conn:
            placeholders = ", ".join(["?"] * len(names))
            rows = conn.execute(
                f"SELECT * from menu WHERE name IN ({placeholders})",
                tuple(names),
            ).fetchall()

            if not rows:
                return None

            items = [self._convert_to_entity(row) for row in rows]
            return set(items)

    def get_all(self) -> set[MenuItem] | None:
        with self._get_connection() as conn:
            rows = conn.execute(
                f"SELECT * from menu",
            ).fetchall()
            
            if not rows:
                return None

            items = [self._convert_to_entity(row) for row in rows]
            return set(items)

    def save(self, item: MenuItem) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                    INSERT INTO menu (name, requires_milk_foam, ingredients, price, category)
                    VALUES(?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                    requires_milk_foam = excluded.requires_milk_foam,
                    ingredients = excluded.ingredients,
                    price = excluded.price,
                    category = excluded.category
                """,
                (
                    item.name,
                    str(item.recipe.requires_milk_foam),
                    adapt_ingredients_dict(item.recipe.ingredients),
                    item.price,
                    str(item.category),
                ),
            )
            
    def delete(self, name: str) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM menu WHERE name = ?", 
                (name,)
            )
            conn.commit()
            

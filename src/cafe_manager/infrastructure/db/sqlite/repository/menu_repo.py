from cafe_manager.application.uow import MenuRepo
from .abstract_repo import *
from cafe_manager.domain.entities.menu import *


class SQLiteMenuRepo(AbstractSQliteRepo, MenuRepo):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection)

    def _init_db(self) -> None:
        self._conn.execute(
            """
                    CREATE TABLE IF NOT EXISTS menu (
                    name TEXT PRIMARY KEY,
                    ingredients INGR_DICT,
                    price MONEY,
                    category TEXT
                )"""
        )

    def _convert_to_entity(self, row: sqlite3.Row) -> MenuItem:
        return MenuItem(
            name=row["name"],
            recipe=Recipe(
                convert_ingredients_dict(row["ingredients"]),
            ),
            price=row["price"],
            category=MenuItemCategory(row["category"]),
        )

    def get_by_name(self, name: str) -> MenuItem | None:
        row = self._conn.execute(
            f"SELECT * from menu WHERE name = ?",
            (name,),
        ).fetchone()

        if not row:
            return None

        return self._convert_to_entity(row)

    def get_all(self) -> set[MenuItem] | None:
        rows = self._conn.execute(
            f"SELECT * from menu",
        ).fetchall()

        if not rows:
            return None

        items = [self._convert_to_entity(row) for row in rows]
        return set(items)

    def save(self, item: MenuItem) -> None:
        self._conn.execute(
            """
                    INSERT INTO menu (name, ingredients, price, category)
                    VALUES(?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                    ingredients = excluded.ingredients,
                    price = excluded.price,
                    category = excluded.category
                """,
            (
                item.name,
                adapt_ingredients_dict(item.recipe.ingredients),
                item.price,
                str(item.category),
            ),
        )

    def delete_by_name(self, name: str) -> None:
        self._conn.execute("DELETE FROM menu WHERE name = ?", (name,))

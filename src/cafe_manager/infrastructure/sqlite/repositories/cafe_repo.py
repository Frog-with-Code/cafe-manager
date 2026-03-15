from pathlib import Path

from .abstract_repo import AbstractSQliteRepo, sqlite3
from cafe_manager.domain.entities.cafe import Cafe


class SQLiteCafeRepo(AbstractSQliteRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cafe_info (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    name TEXT NOT NULL,
                    address TEXT NOT NULL
                )
            """
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> Cafe:
        return Cafe(name=row["name"], address=row["address"])

    def get(self) -> Cafe | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM cafe_info WHERE id = 1").fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def save(self, cafe: Cafe):
        with self._get_connection() as conn:
            conn.execute(
                """
                    INSERT INTO cafe_info (id, name, address) 
                    VALUES (1, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        address = excluded.address
                    """,
                (cafe.name, cafe.address),
            )
            conn.commit()

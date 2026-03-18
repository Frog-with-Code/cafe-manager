from cafe_manager.domain.entities.equipment import Chair
from cafe_manager.infrastructure.interfaces import (
    ChairRepo,
    CoffeeMachineRepo,
    TableRepo,
)
from .abstract_repo import *
from cafe_manager.domain.entities.equipment import *


class SQLiteTableRepo(AbstractSQliteRepo, TableRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                max_places INTEGER, 
                state TEXT, 
                chairs_ids "SET"
                )
            """
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row):
        return Table(
            table_id=row["id"],
            max_places=row["max_places"],
            state=TableState(row["state"]),
            chairs_ids=row["chairs_ids"],
        )

    def get_all(self) -> list[Table] | None:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * from tables").fetchall()

            if not rows:
                return None

            tables = [self._convert_to_entity(row) for row in rows]
            return tables

    def get_by_id(self, table_id: int) -> Table | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from tables WHERE id = ?", (table_id,)
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def save(self, table: Table) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO tables (id, max_places, state, chairs_ids) 
                VALUES(?, ?, ?, ?) 
                ON CONFLICT(id) DO UPDATE SET
                max_places = excluded.max_places,
                state = excluded.state,
                chairs_ids = excluded.chairs_ids
                """,
                (table.table_id, table.max_places, str(table._state), table.chairs_ids),
            )
            conn.commit()

    def save_many(self, tables: list[Table]) -> None:
        with self._get_connection() as conn:
            params = [
                (
                    table.table_id,
                    table.max_places,
                    str(table._state),
                    table.chairs_ids,
                )
                for table in tables
            ]

            conn.executemany(
                """
                INSERT INTO tables (id, max_places, state, chairs_ids) 
                VALUES(?, ?, ?, ?) 
                ON CONFLICT(id) DO UPDATE SET
                max_places = excluded.max_places,
                state = excluded.state,
                chairs_ids = excluded.chairs_ids
            """,
                (params),
            )
            conn.commit()

    def delete_by_id(self, table_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM tables WHERE id = ?", (table_id,))
            conn.commit()


class SQLiteChairRepo(AbstractSQliteRepo, ChairRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                    CREATE TABLE IF NOT EXISTS chairs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER,
                    state TEXT
                    )
                """
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> Chair:
        return Chair(
            chair_id=row["id"], table_id=row["table_id"], state=ChairState(row["state"])
        )

    def get_free(self) -> list[Chair] | None:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                    SELECT * from chairs WHERE state = 'available'
                """
            ).fetchall()

            if not rows:
                return None

            chairs = [self._convert_to_entity(row) for row in rows]
            return chairs

    def get_by_id(self, chair_id: int) -> Chair | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from chairs WHERE id = ?", (chair_id,)
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def delete_by_id(self, chair_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chairs WHERE id = ?", (chair_id,))
            conn.commit()

    def delete_table_by_id(self, table_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE chairs SET table_id = NULL WHERE table_id = ?", (table_id,)
            )

    def get_busy_by_table_id(self, table_id: int) -> list[Chair] | None:
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                        SELECT * from chairs WHERE table_id = ? AND state IN ('reserved', 'occupied')
                    """,
                (table_id,),
            ).fetchall()

            if not rows:
                return None

            chairs = [self._convert_to_entity(row) for row in rows]
            return chairs

    def save(self, chair: Chair) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO chairs (id, table_id, state) 
                VALUES(?, ?, ?) 
                ON CONFLICT(id) DO UPDATE SET
                table_id = excluded.table_id,
                state = excluded.state
                """,
                (chair.chair_id, chair._table_id, str(chair._state)),
            )
            conn.commit()

    def get_all(self) -> list[Chair] | None:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * from chairs").fetchall()

            if not rows:
                return None

            tables = [self._convert_to_entity(row) for row in rows]
            return tables

    def save_many(self, chairs: list[Chair]) -> None:
        with self._get_connection() as conn:
            try:
                params = [
                    (chair.chair_id, chair._table_id, chair._state) for chair in chairs
                ]

                conn.executemany(
                    """
                    INSERT INTO chairs (id, table_id, state) 
                    VALUES(?, ?, ?) 
                    ON CONFLICT(id) DO UPDATE SET
                    table_id = excluded.table_id,
                    state = excluded.state
                """,
                    (params),
                )
                conn.commit()
            except:
                conn.rollback()
                raise


class SQLiteCoffeeMachineRepo(AbstractSQliteRepo, CoffeeMachineRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS coffee_machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT,
                maintenance_limit INTEGER,
                cycles_count INTEGER,
                state TEXT
                )
                """
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> CoffeeMachine:
        return CoffeeMachine(
            model=row["model"],
            machine_id=row["id"],
            maintenance_limit=row["maintenance_limit"],
            cycles_count=row["cycles_count"],
            state=CoffeeMachineState(row["state"]),
        )

    def get_idle(self) -> CoffeeMachine | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from coffee_machines WHERE state = 'idle'"
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def save(self, machine: CoffeeMachine) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO coffee_machines (id, model, maintenance_limit, cycles_count, state)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                model = excluded.model,
                maintenance_limit = excluded.maintenance_limit,
                cycles_count = excluded.cycles_count,
                state = excluded.state
                """,
                (
                    machine.machine_id,
                    machine.model,
                    machine.maintenance_limit,
                    machine.cycles_count,
                    str(machine._state),
                ),
            )
            conn.commit()

    def delete_by_id(self, machine_id: int) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM coffee_machines WHERE id = ?", (machine_id,))
            conn.commit()

    def get_by_id(self, machine_id: int) -> CoffeeMachine | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from coffee_machines WHERE id = ?", (machine_id,)
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def get_all(self) -> list[CoffeeMachine] | None:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * from coffee_machines").fetchall()

            if not rows:
                return None

            machines = [self._convert_to_entity(row) for row in rows]
            return machines

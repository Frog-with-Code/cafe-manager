from cafe_manager.domain.entities.people import Employee
from cafe_manager.infrastructure.interfaces import EmployeeRepo
from .abstract_repo import *
from cafe_manager.domain.entities.people import *


class SQLiteEmployeeRepo(AbstractSQliteRepo, EmployeeRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    state TEXT,
                    rest_start DATETIME
                )
            """
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> Employee:
        return Employee(
            employee_id=row["id"],
            name=row["name"],
            state=EmployeeState(row["state"]),
            rest_start=row["rest_start"],
        )

    def get_most_free(self) -> Employee | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM employees WHERE state = 'free' ORDER BY rest_start ASC"
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def get_by_id(self, employee_id: str) -> Employee | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM employees WHERE id = ?",
                (employee_id,),
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def save(self, employee: Employee) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO employees (id, name, state, rest_start) 
                VALUES(?, ?, ?, ?) 
                ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                state = excluded.state,
                rest_start = excluded.rest_start
                """,
                (
                    employee.employee_id,
                    employee.name,
                    str(employee._state),
                    employee.rest_start,
                ),
            )
            conn.commit()

    def delete_by_id(self, employee_id: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            conn.commit()

    def get_all(self) -> list[Employee] | None:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * from employees")

            if not rows:
                return None

            employees = [self._convert_to_entity(row) for row in rows]
            return employees


class SQLiteClientRepo(AbstractSQliteRepo):
    def __init__(self, db_path: Path | str):
        super().__init__(db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY,
                    total_spent MONEY,
                    orders_amount INTEGER,
                    registered_at DATETIME
                )
                """
            )
            conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> Client:
        return Client(
            client_id=row["id"],
            total_spent=row["total_spent"],
            orders_amount=row["orders_amount"],
            registered_at=row["registered_at"],
        )

    def get_by_id(self, client_id: str) -> Client | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * from clients WHERE id = ?", (client_id,)
            ).fetchone()

            if not row:
                return None

            return self._convert_to_entity(row)

    def save(self, client: Client) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO clients (id, total_spent, orders_amount, registered_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                total_spent = excluded.total_spent,
                orders_amount = excluded.orders_amount, 
                registered_at = excluded.registered_at
                """,
                (
                    client.client_id,
                    client.total_spent,
                    client.orders_amount,
                    client.registered_at,
                ),
            )
            conn.commit()

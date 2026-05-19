from cafe_manager.domain.entities.people import Client, Employee
from cafe_manager.application.uow import ClientRepo, EmployeeRepo
from .abstract_repo import *
from cafe_manager.domain.entities.people import *


class SQLiteEmployeeRepo(AbstractSQliteRepo, EmployeeRepo):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection)

    def _init_db(self) -> None:
        self._conn.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    state TEXT,
                    rest_start DATETIME
                )
            """)

    def _convert_to_entity(self, row: sqlite3.Row) -> Employee:
        return Employee(
            employee_id=row["id"],
            name=row["name"],
            state=EmployeeState(row["state"]),
            rest_start=row["rest_start"],
        )

    def get_most_free(self) -> Employee | None:
        row = self._conn.execute(
            "SELECT * FROM employees WHERE state = 'free' ORDER BY rest_start ASC"
        ).fetchone()

        if not row:
            return None

        return self._convert_to_entity(row)

    def get_by_id(self, employee_id: str) -> Employee | None:
        row = self._conn.execute(
            "SELECT * FROM employees WHERE id = ?",
            (employee_id,),
        ).fetchone()

        if not row:
            return None

        return self._convert_to_entity(row)

    def save(self, employee: Employee) -> None:
        self._conn.execute(
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
        self._conn.commit()

    def delete_by_id(self, employee_id: str) -> None:
        self._conn.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
        self._conn.commit()

    def get_all(self) -> list[Employee] | None:
        rows = self._conn.execute("SELECT * from employees")

        if not rows:
            return None

        employees = [self._convert_to_entity(row) for row in rows]
        return employees


class SQLiteClientRepo(AbstractSQliteRepo, ClientRepo):
    def __init__(self, connection: sqlite3.Connection):
        super().__init__(connection)

    def _init_db(self) -> None:
        self._conn.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    total_spent MONEY,
                    orders_amount INTEGER,
                    registered_at DATETIME
                )
                """)
        self._conn.commit()

    def _convert_to_entity(self, row: sqlite3.Row) -> Client:
        return Client(
            client_id=row["id"],
            name=row["name"],
            total_spent=row["total_spent"],
            orders_amount=row["orders_amount"],
            registered_at=row["registered_at"],
        )

    def get_by_id(self, client_id: str) -> Client | None:
        row = self._conn.execute(
            "SELECT * from clients WHERE id = ?", (client_id,)
        ).fetchone()

        if not row:
            return None

        return self._convert_to_entity(row)

    def get_all(self) -> list[Client] | None:
        rows = self._conn.execute("SELECT * from clients").fetchall()

        if not rows:
            return None

        rows = [self._convert_to_entity(row) for row in rows]
        return rows

    def save(self, client: Client) -> None:
        self._conn.execute(
            """
                INSERT INTO clients (id, name, total_spent, orders_amount, registered_at)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                total_spent = excluded.total_spent,
                orders_amount = excluded.orders_amount, 
                registered_at = excluded.registered_at
                """,
            (
                client.client_id,
                client.name,
                client.total_spent,
                client.orders_amount,
                client.registered_at,
            ),
        )
        self._conn.commit()

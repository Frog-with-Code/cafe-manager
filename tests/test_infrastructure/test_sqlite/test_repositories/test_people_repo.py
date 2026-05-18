import pytest
import sqlite3
from decimal import Decimal
from datetime import datetime, timedelta
from cafe_manager.infrastructure.db.sqlite.repository.people_repo import (
    SQLiteEmployeeRepo,
    SQLiteClientRepo,
)
from cafe_manager.domain.entities.people import Employee, EmployeeState, Client
from cafe_manager.domain.entities.finance import Money


class TestSQLiteEmployeeRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test_people.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteEmployeeRepo(conn)
        repo._init_db()

        yield repo
        conn.close()

    def test_save_and_get_by_id(self, repo):
        emp = Employee(name="Alice", employee_id="emp-1", state=EmployeeState.FREE)
        repo.save(emp)

        retrieved = repo.get_by_id("emp-1")
        assert retrieved is not None
        assert retrieved.name == "Alice"
        assert retrieved._state == EmployeeState.FREE
        assert isinstance(retrieved.rest_start, datetime)

    def test_save_update(self, repo):
        emp = Employee(name="Alice", employee_id="emp-1")
        repo.save(emp)

        emp.work()
        repo.save(emp)

        updated = repo.get_by_id("emp-1")
        assert updated._state == EmployeeState.BUSY

    def test_get_most_free(self, repo):
        now = datetime.now()
        e1 = Employee(name="Busy", employee_id="e1", state=EmployeeState.BUSY)
        e2 = Employee(
            name="Free-New", employee_id="e2", state=EmployeeState.FREE, rest_start=now
        )
        e3 = Employee(
            name="Free-Old",
            employee_id="e3",
            state=EmployeeState.FREE,
            rest_start=now - timedelta(hours=1),
        )

        repo.save(e1)
        repo.save(e2)
        repo.save(e3)

        most_free = repo.get_most_free()
        assert most_free.employee_id == "e3"

    def test_get_all(self, repo):
        repo.save(Employee("E1", "id1"))
        repo.save(Employee("E2", "id2"))

        all_emps = repo.get_all()
        assert len(all_emps) == 2
        ids = [e.employee_id for e in all_emps]
        assert "id1" in ids
        assert "id2" in ids

    def test_delete_by_id(self, repo):
        repo.save(Employee("Target", "del-me"))
        assert repo.get_by_id("del-me") is not None

        repo.delete_by_id("del-me")
        assert repo.get_by_id("del-me") is None

    def test_get_non_existent(self, repo):
        assert repo.get_by_id("ghost") is None


class TestSQLiteClientRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test_people.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteClientRepo(conn)

        yield repo
        conn.close()

    def test_save_and_get_by_id(self, repo):
        client = Client(client_id="cli-1", name="Bob")
        repo.save(client)

        retrieved = repo.get_by_id("cli-1")
        assert retrieved is not None
        assert retrieved.name == "Bob"
        assert retrieved.total_spent == Money(Decimal("0.00"))
        assert retrieved.orders_amount == 0

    def test_save_update_totals(self, repo):
        client = Client(client_id="cli-update", name="Bob")
        repo.save(client)

        client.pay(Money(Decimal("50.00")))
        repo.save(client)

        updated = repo.get_by_id("cli-update")
        assert updated.total_spent == Money(Decimal("50.00"))
        assert updated.orders_amount == 1

    def test_get_non_existent(self, repo):
        assert repo.get_by_id("non-existent") is None

    def test_save_idempotency_registered_at(self, repo):
        dt = datetime(2020, 1, 1)
        client = Client(client_id="cli-id", name="Bob", registered_at=dt)
        repo.save(client)

        retrieved = repo.get_by_id("cli-id")
        assert retrieved.registered_at == dt

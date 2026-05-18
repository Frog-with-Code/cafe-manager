import pytest
import sqlite3
from cafe_manager.infrastructure.db.sqlite.repository.cafe_repo import SQLiteCafeRepo
from cafe_manager.domain.entities.cafe import Cafe


class TestSQLiteCafeRepo:
    @pytest.fixture
    def conn(self, tmp_path):
        db_path = tmp_path / "test_cafe.db"
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row

        yield conn
        conn.close()

    @pytest.fixture
    def repo(self, conn):
        repo = SQLiteCafeRepo(conn)
        return repo

    def test_get_returns_none_when_empty(self, repo):
        assert repo.get() is None

    def test_save_and_get_success(self, repo):
        cafe = Cafe(name="Green Bean", address="123 Coffee St")
        repo.save(cafe)

        retrieved = repo.get()
        assert retrieved is not None
        assert retrieved.name == "Green Bean"
        assert retrieved.address == "123 Coffee St"

    def test_save_updates_existing_record(self, repo):
        initial_cafe = Cafe(name="Old Name", address="Old Address")
        repo.save(initial_cafe)

        updated_cafe = Cafe(name="New Name", address="New Address")
        repo.save(updated_cafe)

        retrieved = repo.get()
        assert retrieved.name == "New Name"
        assert retrieved.address == "New Address"

    def test_singleton_constraint_in_db(self, repo):
        cafe_a = Cafe(name="Cafe A", address="Addr A")
        cafe_b = Cafe(name="Cafe B", address="Addr B")

        repo.save(cafe_a)
        repo.save(cafe_b)

        cursor = repo._conn.execute("SELECT COUNT(*) FROM cafe_info")
        count = cursor.fetchone()[0]
        assert count == 1

    def test_get_after_reinitialization(self, tmp_path):
        db_path = tmp_path / "test_cafe.db"
        conn1 = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn1.row_factory = sqlite3.Row
        repo1 = SQLiteCafeRepo(conn1)
        repo1.save(Cafe(name="Persistent", address="Location"))
        conn1.commit()
        conn1.close()

        conn2 = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn2.row_factory = sqlite3.Row
        repo2 = SQLiteCafeRepo(conn2)
        retrieved = repo2.get()
        conn2.close()

        assert retrieved is not None
        assert retrieved.name == "Persistent"

    def test_save_with_empty_strings(self, repo):
        cafe = Cafe(name="", address="")
        repo.save(cafe)

        retrieved = repo.get()
        assert retrieved.name == ""
        assert retrieved.address == ""

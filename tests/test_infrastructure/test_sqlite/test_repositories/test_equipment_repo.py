import pytest
import sqlite3
from cafe_manager.infrastructure.db.sqlite.repository.equipment_repo import (
    SQLiteTableRepo,
    SQLiteChairRepo,
    SQLiteCoffeeMachineRepo,
)
from cafe_manager.domain.entities.equipment import (
    Table,
    TableState,
    Chair,
    ChairState,
    CoffeeMachine,
    CoffeeMachineState,
)


class TestSQLiteTableRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteTableRepo(conn)

        yield repo
        conn.close()

    def test_save_and_get_by_id(self, repo):
        table = Table(max_places=4, state=TableState.AVAILABLE, chairs_ids={1, 2})
        repo.save(table)

        all_tables = repo.get_all()
        assert len(all_tables) == 1
        t_id = all_tables[0].table_id

        retrieved = repo.get_by_id(t_id)
        assert retrieved.max_places == 4
        assert retrieved._state == TableState.AVAILABLE
        assert retrieved.chairs_ids == {1, 2}

    def test_update_table(self, repo):
        table = Table(max_places=2)
        table.add_chair(1)
        repo.save(table)
        saved = repo.get_all()[0]

        saved.reserve(1)
        saved.add_chair(10)
        repo.save(saved)

        updated = repo.get_by_id(saved.table_id)
        assert updated._state == TableState.RESERVED
        assert 10 in updated.chairs_ids

    def test_save_many_and_get_all(self, repo):
        tables = [Table(max_places=2), Table(max_places=4), Table(max_places=6)]
        repo.save_many(tables)

        all_tables = repo.get_all()
        assert len(all_tables) == 3
        assert {t.max_places for t in all_tables} == {2, 4, 6}

    def test_delete_by_id(self, repo):
        table = Table(max_places=2)
        repo.save(table)
        t_id = repo.get_all()[0].table_id

        repo.delete_by_id(t_id)
        assert repo.get_by_id(t_id) is None


class TestSQLiteChairRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteChairRepo(conn)
        repo._init_db()

        yield repo
        conn.close()

    def test_save_and_get_all(self, repo):
        chair = Chair(table_id=1, state=ChairState.AVAILABLE)
        repo.save(chair)

        chairs = repo.get_all()
        assert len(chairs) == 1
        assert chairs[0]._table_id == 1
        assert chairs[0]._state == ChairState.AVAILABLE

    def test_get_free(self, repo):
        c1 = Chair(state=ChairState.AVAILABLE)
        c2 = Chair(state=ChairState.RESERVED)
        repo.save(c1)
        repo.save(c2)

        free = repo.get_free()
        assert len(free) == 1
        assert free[0]._state == ChairState.AVAILABLE

    def test_get_busy_by_table_id(self, repo):
        c1 = Chair(chair_id=1, table_id=5, state=ChairState.RESERVED)
        c2 = Chair(chair_id=2, table_id=5, state=ChairState.OCCUPIED)
        c3 = Chair(chair_id=3, table_id=5, state=ChairState.AVAILABLE)
        repo.save_many([c1, c2, c3])

        busy = repo.get_busy_by_table_id(5)
        assert len(busy) == 2
        states = {c._state for c in busy}
        assert ChairState.RESERVED in states
        assert ChairState.OCCUPIED in states

    def test_delete_table_by_id(self, repo):
        chair = Chair(chair_id=10, table_id=7)
        repo.save(chair)

        repo.delete_table_by_id(7)
        updated = repo.get_by_id(10)
        assert updated._table_id is None

    def test_delete_by_id(self, repo):
        chair = Chair(chair_id=1)
        repo.save(chair)
        repo.delete_by_id(1)
        assert repo.get_by_id(1) is None


class TestSQLiteCoffeeMachineRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteCoffeeMachineRepo(conn)
        repo._init_db()

        yield repo
        conn.close()

    def test_save_and_get_by_id(self, repo):
        m = CoffeeMachine(model="Delonghi", maintenance_limit=100)
        repo.save(m)

        m_id = repo.get_all()[0].machine_id
        retrieved = repo.get_by_id(m_id)

        assert retrieved.model == "Delonghi"
        assert retrieved.maintenance_limit == 100
        assert retrieved._state == CoffeeMachineState.IDLE

    def test_get_idle(self, repo):
        m1 = CoffeeMachine(model="A", state=CoffeeMachineState.WORKING)
        m2 = CoffeeMachine(model="B", state=CoffeeMachineState.IDLE)
        repo.save(m1)
        repo.save(m2)

        idle = repo.get_idle()
        assert idle.model == "B"

    def test_update_cycles(self, repo):
        m = CoffeeMachine(model="X", cycles_count=10)
        repo.save(m)
        saved = repo.get_all()[0]

        saved.start()
        repo.save(saved)

        updated = repo.get_by_id(saved.machine_id)
        assert updated.cycles_count == 11
        assert updated._state == CoffeeMachineState.WORKING

    def test_delete_by_id(self, repo):
        m = CoffeeMachine(model="Z")
        repo.save(m)
        m_id = repo.get_all()[0].machine_id

        repo.delete_by_id(m_id)
        assert repo.get_by_id(m_id) is None

import pytest
import sqlite3
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from cafe_manager.domain.entities.menu import Ingredient, Unit
from cafe_manager.domain.entities.finance import Money
from cafe_manager.infrastructure.db.sqlite.repository.abstract_repo import (
    adapt_ingredients_dict,
    convert_ingredients_dict,
    AbstractSQliteRepo,
)


class TestIngredientDictHelpers:
    def test_roundtrip_conversion(self):
        ing1 = Ingredient("Coffee", Unit.GRAM)
        ing2 = Ingredient("Milk", Unit.MILLILITER)
        original_dict = {ing1: 15.0, ing2: 250.0}

        serialized = adapt_ingredients_dict(original_dict)
        assert isinstance(serialized, str)

        deserialized = convert_ingredients_dict(serialized)
        assert deserialized == original_dict
        assert isinstance(list(deserialized.keys())[0], Ingredient)

    def test_empty_dict_conversion(self):
        serialized = adapt_ingredients_dict({})
        assert serialized == "[]"
        assert convert_ingredients_dict(serialized) == {}


class TestSqliteAdapters:
    @pytest.fixture
    def db_conn(self, tmp_path):
        db_path = tmp_path / "test_adapters.db"
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row

        yield conn
        conn.close()

    def test_set_adapter_converter(self, db_conn):
        db_conn.execute("CREATE TABLE test_set (data 'SET')")
        original_set = {1, 2, 3}
        db_conn.execute("INSERT INTO test_set (data) VALUES (?)", (original_set,))

        row = db_conn.execute("SELECT data FROM test_set").fetchone()
        assert row["data"] == original_set
        assert isinstance(row["data"], set)

    def test_datetime_adapter_converter(self, db_conn):
        db_conn.execute("CREATE TABLE test_dt (data DATETIME)")
        now = datetime.now()
        db_conn.execute("INSERT INTO test_dt (data) VALUES (?)", (now,))

        row = db_conn.execute("SELECT data FROM test_dt").fetchone()
        assert row["data"] == now
        assert isinstance(row["data"], datetime)

    def test_money_adapter_converter(self, db_conn):
        db_conn.execute("CREATE TABLE test_money (data MONEY)")
        m = Money(Decimal("10.50"))
        db_conn.execute("INSERT INTO test_money (data) VALUES (?)", (m,))

        row = db_conn.execute("SELECT data FROM test_money").fetchone()
        assert row["data"] == m
        assert isinstance(row["data"], Money)

    def test_uuid_adapter_converter(self, db_conn):
        db_conn.execute("CREATE TABLE test_uuid (data UUID)")
        u = uuid4()
        db_conn.execute("INSERT INTO test_uuid (data) VALUES (?)", (u,))

        row = db_conn.execute("SELECT data FROM test_uuid").fetchone()
        assert row["data"] == u
        assert isinstance(row["data"], UUID)


class TestAbstractSqliteRepo:
    class MockRepo(AbstractSQliteRepo):
        def _init_db(self) -> None:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS mock (id INTEGER PRIMARY KEY)"
            )

        def _convert_to_entity(self, row: sqlite3.Row):
            return row["id"]

    def test_abstract_repo_initialization(self, tmp_path):
        db_path = tmp_path / "mock.db"
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        repo = self.MockRepo(conn)

        assert repo._conn is conn
        assert isinstance(repo._conn, sqlite3.Connection)
        conn.close()

    def test_uses_passed_connection(self, tmp_path):
        db_path = tmp_path / "mock.db"
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        repo = self.MockRepo(conn)

        repo._conn.execute("INSERT INTO mock (id) VALUES (1)")
        row = repo._conn.execute("SELECT id FROM mock").fetchone()

        assert repo._convert_to_entity(row) == 1
        conn.close()

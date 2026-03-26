import pytest
import sqlite3
import json
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from cafe_manager.domain.entities.menu import Ingredient, Unit
from cafe_manager.domain.entities.finance import Money
from cafe_manager.infrastructure.sqlite.repositories.abstract_repo import (
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
        return conn

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
            with self._get_connection() as conn:
                conn.execute("CREATE TABLE mock (id INTEGER PRIMARY KEY)")

        def _convert_to_entity(self, row: sqlite3.Row):
            return row["id"]

    def test_abstract_repo_initialization(self, tmp_path):
        db_path = tmp_path / "mock.db"
        repo = self.MockRepo(db_path)

        assert db_path.exists()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='mock'"
            )
            assert cursor.fetchone() is not None

    def test_get_connection_config(self, tmp_path):
        repo = self.MockRepo(tmp_path / "mock.db")
        conn = repo._get_connection()

        assert conn.row_factory == sqlite3.Row
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_db_path_conversion(self, tmp_path):
        repo = self.MockRepo(str(tmp_path / "string_path.db"))
        assert isinstance(repo.db_path, Path)

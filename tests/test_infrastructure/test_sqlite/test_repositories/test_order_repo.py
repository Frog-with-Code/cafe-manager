import pytest
import sqlite3
from decimal import Decimal
from datetime import datetime, timedelta
from cafe_manager.infrastructure.db.sqlite.repository.order_repo import SQLiteOrderRepo
from cafe_manager.domain.entities.order import Order, OrderState
from cafe_manager.domain.entities.menu import (
    MenuItem,
    Recipe,
    MenuItemCategory,
    Ingredient,
    Unit,
)
from cafe_manager.domain.entities.finance import Money


class TestSQLiteOrderRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test_orders.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteOrderRepo(conn)

        yield repo
        conn.close()

    @pytest.fixture
    def sample_item(self):
        ing = Ingredient("Coffee Beans", Unit.GRAM)
        recipe = Recipe(ingredients={ing: 15.0})
        return MenuItem(
            name="Espresso",
            recipe=recipe,
            price=Money(Decimal("5.00")),
            category=MenuItemCategory.COFFEE,
        )

    def test_save_and_get_by_id(self, repo, sample_item):
        order = Order(
            order_id="ord-100", items={sample_item: 2}, table_id=1, client_id="cli-1"
        )
        repo.save(order)

        retrieved = repo.get_by_id("ord-100")
        assert retrieved is not None
        assert retrieved.order_id == "ord-100"
        assert retrieved.table_id == 1
        assert retrieved.total_price == Money(Decimal("10.00"))
        assert retrieved._state == OrderState.AWAITING_PAYMENT

        items = retrieved.items
        assert len(items) == 1
        retrieved_item = list(items.keys())[0]
        assert retrieved_item.name == "Espresso"
        assert items[retrieved_item] == 2

    def test_save_update(self, repo, sample_item):
        order = Order(order_id="ord-update", items={sample_item: 1})
        repo.save(order)

        order.pay()
        order.start_cooking("emp-99")
        repo.save(order)

        retrieved = repo.get_by_id("ord-update")
        assert retrieved._state == OrderState.IN_PROGRESS
        assert retrieved.employee_id == "emp-99"
        assert retrieved.paid_at is not None

    def test_get_oldest_paid(self, repo, sample_item):
        now = datetime.now()
        o1 = Order(
            order_id="o1", items={sample_item: 1}, state=OrderState.PAID, paid_at=now
        )
        o2 = Order(
            order_id="o2",
            items={sample_item: 1},
            state=OrderState.PAID,
            paid_at=now - timedelta(minutes=10),
        )
        o3 = Order(
            order_id="o3", items={sample_item: 1}, state=OrderState.AWAITING_PAYMENT
        )

        repo.save(o1)
        repo.save(o2)
        repo.save(o3)

        oldest = repo.get_oldest_paid()
        assert oldest.order_id == "o2"

    def test_get_cooking_from_oldest(self, repo, sample_item):
        now = datetime.now()
        o1 = Order(
            order_id="o1",
            items={sample_item: 1},
            state=OrderState.IN_PROGRESS,
            paid_at=now,
        )
        o2 = Order(
            order_id="o2",
            items={sample_item: 1},
            state=OrderState.IN_PROGRESS,
            paid_at=now - timedelta(minutes=5),
        )

        repo.save(o1)
        repo.save(o2)

        paid_orders = repo.get_cooking_from_oldest()
        assert len(paid_orders) == 2
        assert paid_orders[0].order_id == "o2"
        assert paid_orders[1].order_id == "o1"

    def test_get_active_by_table_id(self, repo, sample_item):
        o1 = Order(
            order_id="o1", items={sample_item: 1}, table_id=10, state=OrderState.PAID
        )
        o2 = Order(
            order_id="o2",
            items={sample_item: 1},
            table_id=10,
            state=OrderState.COMPLETED,
        )
        o3 = Order(
            order_id="o3", items={sample_item: 1}, table_id=20, state=OrderState.PAID
        )

        # Note: COMPLETED status isn't explicitly in entity logic yet, but repo filters it
        o2._state = OrderState.COMPLETED

        repo.save(o1)
        repo.save(o2)
        repo.save(o3)

        active_table_10 = repo.get_active_by_table_id(10)
        assert len(active_table_10) == 1
        assert active_table_10[0].order_id == "o1"

    def test_get_all_active(self, repo, sample_item):
        o1 = Order(
            order_id="o1", items={sample_item: 1}, state=OrderState.AWAITING_PAYMENT
        )
        o2 = Order(order_id="o2", items={sample_item: 1}, state=OrderState.READY)
        o3 = Order(order_id="o3", items={sample_item: 1})
        o3._state = OrderState.COMPLETED

        repo.save(o1)
        repo.save(o2)
        repo.save(o3)

        active = repo.get_all_active()
        assert len(active) == 2
        ids = [o.order_id for o in active]
        assert "o1" in ids
        assert "o2" in ids
        assert "o3" not in ids

    def test_get_non_existent(self, repo):
        assert repo.get_by_id("non-existent") is None

    def test_empty_active_queries(self, repo):
        assert repo.get_all_active() is None
        assert repo.get_oldest_paid() is None

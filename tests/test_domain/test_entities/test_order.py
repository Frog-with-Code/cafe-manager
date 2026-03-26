import pytest
from datetime import datetime
from decimal import Decimal
from cafe_manager.domain.entities.order import Order, OrderState
from cafe_manager.domain.entities.menu import MenuItem, Recipe, MenuItemCategory
from cafe_manager.domain.entities.finance import Money
from cafe_manager.common.exceptions import OrderIsEmptyError, OrderStateError, TableStateError

class TestOrder:
    @pytest.fixture
    def sample_item(self):
        return MenuItem(
            name="Coffee",
            recipe=Recipe(ingredients={}),
            price=Money(Decimal("5.00")),
            category=MenuItemCategory.COFFEE
        )

    def test_order_initialization_success(self, sample_item):
        items = {sample_item: 2}
        order = Order(order_id="ord-1", items=items, table_id=5)
        
        assert order.order_id == "ord-1"
        assert order.table_id == 5
        assert order.total_price == Money(Decimal("10.00"))
        assert order._state == OrderState.AWAITING_PAYMENT
        assert isinstance(order.created_at, datetime)

    def test_order_empty_items_raises_error(self):
        with pytest.raises(OrderIsEmptyError):
            Order(order_id="ord-1", items={})

    def test_items_property_returns_copy(self, sample_item):
        items = {sample_item: 1}
        order = Order(order_id="ord-1", items=items)
        
        retrieved_items = order.items
        retrieved_items[sample_item] = 99
        
        assert order.items[sample_item] == 1

    def test_pay_success(self, sample_item):
        order = Order(order_id="ord-1", items={sample_item: 1})
        order.pay()
        
        assert order._state == OrderState.PAID
        assert isinstance(order.paid_at, datetime)

    def test_pay_invalid_state(self, sample_item):
        order = Order(order_id="ord-1", items={sample_item: 1}, state=OrderState.READY)
        with pytest.raises(OrderStateError):
            order.pay()

    def test_start_cooking_success(self, sample_item):
        order = Order(order_id="ord-1", items={sample_item: 1}, state=OrderState.PAID)
        order.start_cooking(employee_id="emp-1")
        
        assert order._state == OrderState.IN_PROGRESS
        assert order.employee_id == "emp-1"

    def test_start_cooking_invalid_state(self, sample_item):
        order = Order(order_id="ord-1", items={sample_item: 1}, state=OrderState.AWAITING_PAYMENT)
        with pytest.raises(TableStateError):
            order.start_cooking("emp-1")

    def test_end_cooking_success(self, sample_item):
        order = Order(
            order_id="ord-1", 
            items={sample_item: 1}, 
            state=OrderState.IN_PROGRESS, 
            employee_id="emp-1"
        )
        order.end_cooking()
        
        assert order._state == OrderState.READY

    def test_end_cooking_invalid_state(self, sample_item):
        order = Order(order_id="ord-1", items={sample_item: 1}, state=OrderState.PAID)
        with pytest.raises(OrderStateError):
            order.end_cooking()

    def test_calculate_price_with_none(self):
        order = Order(order_id="ord-1", items={MenuItem(
            name="X", 
            recipe=Recipe({}), 
            price=Money(Decimal("1")), 
            category=MenuItemCategory.TEA
        ): 1})
        assert order._calculate_price(None) == Money(Decimal("0.00"))
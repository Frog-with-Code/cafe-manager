import pytest
from decimal import Decimal
from uuid import uuid4
from cafe_manager.domain.services.payment_service import PaymentService, DefaultPaymentService
from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.domain.entities.order import Order, OrderState
from cafe_manager.domain.entities.people import Client
from cafe_manager.domain.entities.menu import MenuItem, Recipe, MenuItemCategory
from cafe_manager.common.exceptions import InsufficientBudgetError

class TestPaymentService:
    @pytest.fixture
    def service(self):
        return DefaultPaymentService()

    @pytest.fixture
    def sample_order(self):
        item = MenuItem(
            name="Espresso",
            recipe=Recipe(ingredients={}),
            price=Money(Decimal("5.00")),
            category=MenuItemCategory.COFFEE
        )
        return Order(order_id="ord-123", items={item: 1})

    @pytest.fixture
    def sample_account(self):
        return Account(account_id=uuid4(), balance=Money(Decimal("100.00")))

    @pytest.fixture
    def sample_client(self):
        return Client(client_id="cli-456", name="John Doe")

    def test_process_payment_success_with_client(self, service, sample_order, sample_account, sample_client):
        cash = Money(Decimal("10.00"))
        order_price = sample_order.total_price # 5.00
        
        u_order, u_account, u_client = service.process(
            order=sample_order,
            account=sample_account,
            client=sample_client,
            cash_provided=cash
        )

        assert u_order._state == OrderState.PAID
        assert u_order.client_id == "cli-456"
        assert u_account.balance == Money(Decimal("105.00"))
        assert u_client.total_spent == order_price
        assert u_client.orders_amount == 1
        assert len(u_account.history) == 1
        assert "cli-456" in u_account.history[0].description

    def test_process_payment_success_without_client(self, service, sample_order, sample_account):
        cash = Money(Decimal("5.00"))
        
        u_order, u_account, u_client = service.process(
            order=sample_order,
            account=sample_account,
            client=None,
            cash_provided=cash
        )

        assert u_order._state == OrderState.PAID
        assert u_order.client_id is None
        assert u_account.balance == Money(Decimal("105.00"))
        assert u_client is None

    def test_process_payment_insufficient_cash(self, service, sample_order, sample_account):
        cash = Money(Decimal("4.00"))
        
        with pytest.raises(InsufficientBudgetError) as excinfo:
            service.process(
                order=sample_order,
                account=sample_account,
                client=None,
                cash_provided=cash
            )
        
        assert "5.00" in str(excinfo.value)
        assert "4.00" in str(excinfo.value)

    def test_process_payment_exact_cash(self, service, sample_order, sample_account):
        cash = Money(Decimal("5.00"))
        
        u_order, _, _ = service.process(
            order=sample_order,
            account=sample_account,
            client=None,
            cash_provided=cash
        )
        
        assert u_order._state == OrderState.PAID

    def test_process_payment_updates_order_paid_at(self, service, sample_order, sample_account):
        assert sample_order.paid_at is None
        
        service.process(
            order=sample_order,
            account=sample_account,
            client=None,
            cash_provided=Money(Decimal("5.00"))
        )
        
        assert sample_order.paid_at is not None
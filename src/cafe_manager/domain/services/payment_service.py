from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.entities.people import Client

from cafe_manager.common.exceptions import InsufficientBudgetError


class PaymentService:
    def process(
        self,
        order: Order,
        account: Account,
        client: Client | None,
        cash_provided: Money,
    ) -> tuple[Order, Account, Client | None]:
        if cash_provided < order.total_price:
            raise InsufficientBudgetError(
                f"Order price = {order.total_price}. {cash_provided} was provided"
            )

        cash = order.total_price

        source_str = f" from client {client.client_id}" if client else ""
        account.add_income(cash, f"Payment for order {order.order_id}" + source_str)
        if client:
            client.pay(cash)
            order.client_id = client.client_id
        order.pay()

        return order, account, client

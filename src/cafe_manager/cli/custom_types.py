import typer

from cafe_manager.domain.entities.finance import Money

from cafe_manager.common.exceptions import IncorrectMoneyAmountError


def parse_money(value: str) -> Money:
    try:
        money = Money.from_any(value)
        return money
    except (IncorrectMoneyAmountError, ValueError) as e:
        raise typer.BadParameter(
            f"Impossible to set '{value}' as money amount. It should be non negative numeric value"
        )

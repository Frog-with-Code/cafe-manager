import typer
from cafe_manager.common.exceptions import IncorrectMoneyAmountError
from cafe_manager.domain.entities.finance import Money


def parse_money(value: str) -> Money:
    try:
        money = Money.from_any(value)
        return money
    except (IncorrectMoneyAmountError, ValueError) as e:
        raise typer.BadParameter(
            f"Impossible to set '{value}' as money amount. It should be non negative numeric value"
        )

import typer

def validate_item_format(item: str) -> tuple[str, int]:
    if ":" not in item:
        raise typer.BadParameter(
            f"Format {item} is incorrect. 'name:amount' is expected"
        )
    name, amount_str = item.split(":")

    try:
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError as e:
        raise typer.BadParameter(
            f"Menu items amount must be integer number > 0. {amount_str} was provided"
        )

    return name, amount


def validate_non_negative(num: int | float | None) -> int | float | None:
    if num is None:
        return None
    
    if num < 0:
        raise typer.BadParameter(
            f"Value must be integer number >= 0. {num} was provided"
        )

    return num


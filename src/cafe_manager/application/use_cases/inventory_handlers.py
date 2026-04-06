from uuid import UUID

from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import Ingredient, Unit

from cafe_manager.application.interfaces import UnitOfWork

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    IngredientExistsError,
    IngredientNotFoundError,
)


class InventoryAddHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(
        self,
        name: str,
        unit: Unit,
        overwrite: bool,
    ) -> None:
        with self._uow as uow:
            ingredient = Ingredient(name, unit)
            if not overwrite and uow.inventory_repo.get_by_names({name}):
                raise IngredientExistsError(
                    f"Ingredient with name '{name}' already exists"
                )

            uow.inventory_repo.save_many({ingredient: 0})


class InventoryRemoveHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, name: str) -> None:
        with self._uow as uow:
            if uow.inventory_repo.get_by_names({name}) is None:
                raise IngredientNotFoundError(
                    f"Ingredient item with name '{name}' was not found"
                )

            uow.inventory_repo.delete_by_name(name)


class InventoryInfoHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self) -> dict[Ingredient, float]:
        with self._uow as uow:
            inventory = uow.inventory_repo.get_all()
            return inventory if inventory else {}


class InventorySupplyHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(
        self, name: str, amount: float, price: Money, account_id: UUID | None
    ) -> None:
        with self._uow as uow:
            if uow.inventory_repo.get_by_names({name}) is None:
                raise IngredientNotFoundError(
                    f"Ingredient with name '{name}' was not found"
                )

            account = (
                uow.finance_repo.get_by_id(account_id)
                if account_id
                else uow.finance_repo.get_primary()
            )
            if account is None:
                raise AccountNotFoundError("Account was not found")

            account.add_expense(
                price, f"Supply inventory with {name} in amount of {amount}"
            )

            uow.finance_repo.save(account)
            uow.inventory_repo.add_ingredient_by_name(name, amount)

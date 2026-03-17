from uuid import UUID
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    IngredientExistsError,
    IngredientNotFoundError,
)
from cafe_manager.domain.entities.finance import Money
from cafe_manager.domain.entities.menu import Ingredient, Unit
from cafe_manager.infrastructure.interfaces import FinanceRepo, InventoryRepo


class InventoryAddHandler:
    def __init__(self, inventory_repo: InventoryRepo) -> None:
        self._inventory_repo = inventory_repo

    def handle(
        self,
        name: str,
        unit: Unit,
        overwrite: bool,
    ) -> None:
        ingredient = Ingredient(name, unit)
        if not overwrite and self._inventory_repo.get_by_names({name}):
            raise IngredientExistsError(f"Ingredient with name '{name}' already exists")

        self._inventory_repo.save_many({ingredient: 0})


class InventoryRemoveHandler:
    def __init__(self, inventory_repo: InventoryRepo) -> None:
        self._inventory_repo = inventory_repo

    def handle(self, name: str) -> None:
        if self._inventory_repo.get_by_names({name}) is None:
            raise IngredientNotFoundError(
                f"Ingredient item with name '{name}' was not found"
            )

        self._inventory_repo.delete_by_name(name)


class InventoryInfoHandler:
    def __init__(self, inventory_repo: InventoryRepo) -> None:
        self._inventory_repo = inventory_repo

    def handle(self) -> dict[Ingredient, float]:
        inventory = self._inventory_repo.get_all()
        return inventory if inventory else {}


class InventorySupplyHandler:
    def __init__(
        self, inventory_repo: InventoryRepo, finance_repo: FinanceRepo
    ) -> None:
        self._inventory_repo = inventory_repo
        self._finance_repo = finance_repo

    def handle(
        self, name: str, amount: float, price: Money, account_id: UUID | None
    ) -> None:
        if self._inventory_repo.get_by_names({name}) is None:
            raise IngredientNotFoundError(
                f"Ingredient with name '{name}' was not found"
            )

        account = (
            self._finance_repo.get_by_id(account_id)
            if account_id
            else self._finance_repo.get_primary()
        )
        if account is None:
            raise AccountNotFoundError("Account was not found")

        account.add_expense(
            price, f"Supply inventory with {name} in amount of {amount}"
        )

        self._finance_repo.save(account)
        self._inventory_repo.add_ingredient_by_name(name, amount)

from uuid import UUID
from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CoffeeMachineNotFoundError,
    InsufficientBudgetError,
)
from cafe_manager.domain.entities.equipment import CoffeeMachine
from cafe_manager.domain.entities.finance import Money
from cafe_manager.application.interfaces import CoffeeMachineRepo, FinanceRepo


class CoffeeMachineBuyHandler:
    def __init__(
        self, finance_repo: FinanceRepo, machine_repo: CoffeeMachineRepo
    ) -> None:
        self._finance_repo = finance_repo
        self._machine_repo = machine_repo

    def handle(
        self, price: Money, model: str, limit: int, account_id: UUID | None
    ) -> None:
        account = (
            self._finance_repo.get_by_id(account_id)
            if account_id
            else self._finance_repo.get_primary()
        )
        if account is None:
            raise AccountNotFoundError(f"Account was not found")

        if account.balance < price:
            raise InsufficientBudgetError(
                f"Not enough money to buy coffee-machine for {str(price)}"
            )

        account.add_expense(price, f"Buy coffee-machine of model '{model}'")
        machine = CoffeeMachine(model=model, maintenance_limit=limit)

        self._finance_repo.save(account)
        self._machine_repo.save(machine)


class CoffeeMachineDiscardHandler:
    def __init__(self, machine_repo: CoffeeMachineRepo) -> None:
        self._machine_repo = machine_repo

    def handle(self, machine_id: int) -> None:
        if self._machine_repo.get_by_id(machine_id) is None:
            raise CoffeeMachineNotFoundError(
                f"Coffee-machine with id {machine_id} was not found"
            )

        self._machine_repo.delete_by_id(machine_id)


class CoffeeMachineInfoHandler:
    def __init__(self, machine_repo: CoffeeMachineRepo) -> None:
        self._machine_repo = machine_repo

    def handle(self) -> list[CoffeeMachine]:
        machines = self._machine_repo.get_all()
        return machines if machines else []
    
class CoffeeMachineServiceHandler:
    def __init__(self, machine_repo: CoffeeMachineRepo) -> None:
        self._machine_repo = machine_repo
        
    def handle(self, machine_id: int) -> None:
        machine = self._machine_repo.get_by_id(machine_id)
        if machine is None:
            raise CoffeeMachineNotFoundError(f"Coffee-machine with ID {machine_id} was not found")
        
        machine.service()
        
class CoffeeMachineResumeHandler:
    def __init__(self, machine_repo: CoffeeMachineRepo) -> None:
        self._machine_repo = machine_repo
        
    def handle(self, machine_id: int) -> None:
        machine = self._machine_repo.get_by_id(machine_id)
        if machine is None:
            raise CoffeeMachineNotFoundError(f"Coffee-machine with ID {machine_id} was not found")
        
        machine.resume()

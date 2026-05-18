from uuid import UUID

from cafe_manager.domain.entities.equipment import CoffeeMachine
from cafe_manager.domain.entities.finance import Money
from cafe_manager.application.uow import UnitOfWork

from cafe_manager.common.exceptions import (
    AccountNotFoundError,
    CoffeeMachineNotFoundError,
    InsufficientBudgetError,
)


class CoffeeMachineBuyHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(
        self, price: Money, model: str, limit: int, account_id: UUID | None
    ) -> None:
        with self._uow as uow:
            account = (
                uow.finance_repo.get_by_id(account_id)
                if account_id
                else uow.finance_repo.get_primary()
            )
            if account is None:
                raise AccountNotFoundError(f"Account was not found")

            if account.balance < price:
                raise InsufficientBudgetError(
                    f"Not enough money to buy coffee-machine for {str(price)}"
                )

            account.add_expense(price, f"Buy coffee-machine of model '{model}'")
            machine = CoffeeMachine(model=model, maintenance_limit=limit)

            uow.finance_repo.save(account)
            uow.machine_repo.save(machine)


class CoffeeMachineDiscardHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, machine_id: int) -> None:
        with self._uow as uow:
            if uow.machine_repo.get_by_id(machine_id) is None:
                raise CoffeeMachineNotFoundError(
                    f"Coffee-machine with id {machine_id} was not found"
                )

            uow.machine_repo.delete_by_id(machine_id)


class CoffeeMachineInfoHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self) -> list[CoffeeMachine]:
        with self._uow as uow:
            machines = uow.machine_repo.get_all()
            return machines if machines else []


class CoffeeMachineServiceHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, machine_id: int) -> None:
        with self._uow as uow:
            machine = uow.machine_repo.get_by_id(machine_id)
            if machine is None:
                raise CoffeeMachineNotFoundError(
                    f"Coffee-machine with ID {machine_id} was not found"
                )

            machine.service()


class CoffeeMachineResumeHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, machine_id: int) -> None:
        with self._uow as uow:
            machine = uow.machine_repo.get_by_id(machine_id)
            if machine is None:
                raise CoffeeMachineNotFoundError(
                    f"Coffee-machine with ID {machine_id} was not found"
                )

            machine.resume()

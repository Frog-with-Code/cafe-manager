from typing import Protocol
from uuid import UUID

from cafe_manager.domain.entities.people import Client, Employee
from cafe_manager.domain.entities.equipment import Table, Chair, CoffeeMachine
from cafe_manager.domain.entities.menu import Ingredient, MenuItem
from cafe_manager.domain.entities.finance import Account
from cafe_manager.domain.entities.order import Order
from cafe_manager.domain.entities.cafe import Cafe


class EmployeeRepo(Protocol):
    def get_most_free(self) -> Employee | None:
        pass

    def get_by_id(self, employee_id: str) -> Employee | None:
        pass

    def save(self, employee: Employee) -> None:
        pass
    
    def delete_by_id(self, employee_id: str) -> None:
        pass
    
    def get_all(self) -> list[Employee] | None:
        pass


class FinanceRepo(Protocol):
    def get_by_id(self, account_id: UUID) -> Account | None:
        pass

    def save(self, account: Account) -> None:
        pass
    
    def set_primary(self, account_id: UUID) -> None:
        pass
    
    def get_primary(self) -> Account | None:
        pass


class TableRepo(Protocol):
    def get_all(self) -> list[Table] | None:
        pass

    def get_by_id(self, table_id: int) -> Table | None:
        pass

    def save(self, table: Table) -> None:
        pass

    def save_many(self, tables: list[Table]) -> None:
        pass
    
    def delete_by_id(self, table_id: int) -> None:
        pass


class ChairRepo(Protocol):
    def get_free(self) -> list[Chair] | None:
        pass
    
    def get_by_id(self, chair_id: int) -> Chair | None:
        pass

    def get_busy_by_table_id(self, table_id: int) -> list[Chair] | None:
        pass

    def save(self, chair: Chair) -> None:
        pass

    def save_many(self, chairs: list[Chair]) -> None:
        pass
    
    def delete_by_id(self, chair_id: int) -> None:
        pass
    
    def delete_table_by_id(self, table_id: int) -> None:
        pass
    
    def get_all(self) -> list[Chair] | None:
        pass


class InventoryRepo(Protocol):
    def get_by_names(self, names: set[str]) -> dict[Ingredient, float] | None:
        pass

    def save_many(self, inventory: dict[Ingredient, float]) -> None:
        pass


class OrderRepo(Protocol):
    def get_by_id(self, order_id: str) -> Order | None:
        pass

    def get_oldest_paid(self) -> Order | None:
        pass

    def get_paid_from_oldest(self) -> list[Order] | None:
        pass
    
    def get_active_by_table_id(self, table_id: int) -> list[Order] | None:
        pass

    def save(self, order: Order) -> None:
        pass


class CoffeeMachineRepo(Protocol):
    def get_free(self) -> CoffeeMachine | None:
        pass

    def save(self, machine: CoffeeMachine) -> None:
        pass


class MenuRepo(Protocol):
    def get_by_names(self, names: set[str]) -> set[MenuItem] | None:
        pass
    
    def get_all(self) -> set[MenuItem] | None:
        pass

    def save(self, item: MenuItem) -> None:
        pass
    
    def delete_by_name(self, name: str) -> None:
        pass


class ClientRepo(Protocol):
    def get_by_id(self, client_id: str) -> Client | None:
        pass

    def save(self, client: Client) -> None:
        pass


class CafeRepo(Protocol):
    def get(self) -> Cafe | None:
        pass

    def save(self, cafe: Cafe) -> None:
        pass

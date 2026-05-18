from typing import Protocol

from cafe_manager.domain.repository import (
    CafeRepo,
    ChairRepo,
    ClientRepo,
    CoffeeMachineRepo,
    EmployeeRepo,
    FinanceRepo,
    InventoryRepo,
    MenuRepo,
    OrderRepo,
    TableRepo,
)


class UnitOfWork(Protocol):
    cafe_repo: CafeRepo
    order_repo: OrderRepo
    inventory_repo: InventoryRepo
    menu_repo: MenuRepo
    table_repo: TableRepo
    chair_repo: ChairRepo
    finance_repo: FinanceRepo
    employee_repo: EmployeeRepo
    client_repo: ClientRepo
    machine_repo: CoffeeMachineRepo

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

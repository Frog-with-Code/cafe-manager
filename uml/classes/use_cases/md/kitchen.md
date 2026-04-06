```mermaid
---
config:
  layout: elk
---

classDiagram
    direction LR
    class UnitOfWork {
        <<Interface>>
    }

    class IngredientCalculator {
    }


    class KitchenStartHandler {
        #_uow: UnitOfWork
        #_ingredient_calculator: IngredientCalculator
        +handle(employee_id: str) tuple
        #_start_coffee_machine(order: Order) tuple
        #_get_employee(employee_id: str) Employee
    }

    class KitchenListPending {
        #_uow: UnitOfWork
        +handle() list~Order~
    }

    class KitchenReadyHandler {
        #_uow: UnitOfWork
        +handle(order_id: str)
        #_stop_coffee_machine(machine_id: int) CoffeeMachine
    }

    KitchenStartHandler --> UnitOfWork
    KitchenStartHandler --> IngredientCalculator

    UnitOfWork <-- KitchenListPending 
    UnitOfWork <-- KitchenReadyHandler

```
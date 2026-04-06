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

    class IDGeneratingService {
    }

    class EmployeeHireHandler {
        #_uow: UnitOfWork
        #_id_generator: IDGeneratingService
        +handle(name: str) str
    }

    class EmployeeFireHandler {
        #_uow: UnitOfWork
        +handle(employee_id: str) None
    }

    class EmployeeInfoHandler {
        #_uow: UnitOfWork
        +handle() list~Employee~
    }

    class EmployeeCreateAtmosphere {
        +jokes: list~str~
        #_uow: UnitOfWork
        +handle() str
        #_get_random_joke() str
    }

    EmployeeHireHandler --> UnitOfWork
    EmployeeHireHandler --> IDGeneratingService
    EmployeeFireHandler --> UnitOfWork

    UnitOfWork <-- EmployeeInfoHandler
    UnitOfWork <-- EmployeeCreateAtmosphere
```
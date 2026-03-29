```mermaid
---
config:
  layout: elk
---

classDiagram
    direction LR
    class FinanceRepo {
        <<Interface>>
    }

    class FinanceInvestHandler {
        #_finance_repo: FinanceRepo
        +handle(amount: Money, account_id: UUID, message: str) None
    }

    class FinanceStatsHandler {
        #_finance_repo: FinanceRepo
        +handle(account_id: UUID, start_date: datetime, end_date: datetime) dict~str, Any~
    }

    class FinanceHistoryHandler {
        #_finance_repo: FinanceRepo
        +handle(account_id: UUID, limit: int) list~Transaction~
    }

    class FinanceSetPrimaryHandler {
        #_finance_repo: FinanceRepo
        +handle(account_id: UUID) None
    }

    FinanceInvestHandler --> FinanceRepo
    FinanceStatsHandler --> FinanceRepo

    FinanceRepo <-- FinanceHistoryHandler
    FinanceRepo <-- FinanceSetPrimaryHandler

```
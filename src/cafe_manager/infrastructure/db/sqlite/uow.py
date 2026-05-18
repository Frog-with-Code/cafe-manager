import sqlite3
from pathlib import Path

from cafe_manager.application.uow import UnitOfWork
from .repository import *


class SQLiteUnitOfWork(UnitOfWork):
    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)

    def __enter__(self) -> "UnitOfWork":
        self._conn = sqlite3.connect(
            self._db_path, detect_types=sqlite3.PARSE_DECLTYPES
        )
        self._conn.row_factory = sqlite3.Row

        self.order_repo = SQLiteOrderRepo(self._conn)
        self.inventory_repo = SQLiteInventoryRepo(self._conn)
        self.menu_repo = SQLiteMenuRepo(self._conn)
        self.table_repo = SQLiteTableRepo(self._conn)
        self.chair_repo = SQLiteChairRepo(self._conn)
        self.machine_repo = SQLiteCoffeeMachineRepo(self._conn)
        self.finance_repo = SQLiteFinanceRepo(self._conn)
        self.employee_repo = SQLiteEmployeeRepo(self._conn)
        self.client_repo = SQLiteClientRepo(self._conn)
        self.cafe_repo = SQLiteCafeRepo(self._conn)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._conn is None:
            return

        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
        finally:
            self._conn.close()
            self._conn = None

    def commit(self) -> None:
        if self._conn:
            self._conn.commit()

    def rollback(self) -> None:
        if self._conn:
            self._conn.rollback()

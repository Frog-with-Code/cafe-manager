import pytest
import sqlite3
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from cafe_manager.common.exceptions import AccountNotFoundError
from cafe_manager.infrastructure.sqlite.repositories.finance_repo import SQLiteFinanceRepo
from cafe_manager.domain.entities.finance import Account, Transaction, TransactionType, Money

class TestSQLiteFinanceRepo:
    @pytest.fixture
    def repo(self, tmp_path):
        conn = sqlite3.connect(
            tmp_path / "test_finance.db", detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        repo = SQLiteFinanceRepo(conn)
        
        yield repo
        conn.close()

    def test_save_and_get_by_id(self, repo):
        acc_id = uuid4()
        balance = Money(Decimal("1000.50"))
        account = Account(account_id=acc_id, balance=balance)
        
        repo.save(account)
        
        retrieved = repo.get_by_id(acc_id)
        assert retrieved is not None
        assert retrieved.account_id == acc_id
        assert retrieved.balance == balance
        assert len(retrieved.history) == 0

    def test_save_with_history(self, repo):
        account = Account(balance=Money(Decimal("500.00")))
        account.add_income(Money(Decimal("100.00")), "Test Income")
        account.add_expense(Money(Decimal("50.00")), "Test Expense")
        
        repo.save(account)
        
        retrieved = repo.get_by_id(account.account_id)
        assert len(retrieved.history) == 2
        
        history_types = [t.transaction_type for t in retrieved.history]
        assert TransactionType.INCOME in history_types
        assert TransactionType.EXPENSE in history_types
        assert retrieved.balance == Money(Decimal("550.00"))

    def test_update_balance_only(self, repo):
        account = Account(balance=Money(Decimal("100.00")))
        repo.save(account)
        
        account._balance = Money(Decimal("200.00"))
        repo.save(account)
        
        retrieved = repo.get_by_id(account.account_id)
        assert retrieved.balance == Money(Decimal("200.00"))

    def test_primary_account_logic(self, repo):
        acc1 = Account(balance=Money(Decimal("10.00")))
        acc2 = Account(balance=Money(Decimal("20.00")))
        repo.save(acc1)
        repo.save(acc2)
        
        assert repo.get_primary() is None
        
        repo.set_primary(acc1.account_id)
        primary = repo.get_primary()
        assert primary.account_id == acc1.account_id
        
        repo.set_primary(acc2.account_id)
        new_primary = repo.get_primary()
        assert new_primary.account_id == acc2.account_id
        assert new_primary.account_id != acc1.account_id

    def test_set_primary_not_found(self, repo):
        with pytest.raises(AccountNotFoundError):
            repo.set_primary(uuid4())

    def test_get_transactions_by_period(self, repo):
        account = Account(balance=Money(Decimal("1000.00")))
        repo.save(account)
        
        now = datetime.now()
        t1 = Transaction(TransactionType.INCOME, Money(Decimal("10")), "Old", time=now - timedelta(days=5))
        t2 = Transaction(TransactionType.INCOME, Money(Decimal("20")), "Mid", time=now - timedelta(days=2))
        t3 = Transaction(TransactionType.INCOME, Money(Decimal("30")), "Now", time=now)
        
        account._history = [t1, t2, t3]
        repo.save(account)
        
        # Filter mid period
        start = now - timedelta(days=3)
        end = now - timedelta(days=1)
        
        results = repo.get_transactions_by_period(account.account_id, start, end)
        assert len(results) == 1
        assert results[0].description == "Mid"

    def test_get_latest_transactions(self, repo):
        account = Account(balance=Money(Decimal("100.00")))
        for i in range(15):
            account.add_income(Money(Decimal(str(i))), f"Income {i}")
        
        repo.save(account)
        
        latest = repo.get_latest_transactions(account.account_id, limit=5)
        assert len(latest) == 5
        assert latest[0].description == "Income 14"
        assert latest[4].description == "Income 10"

    def test_get_non_existent(self, repo):
        assert repo.get_by_id(uuid4()) is None

    def test_save_history_idempotency(self, repo):
        account = Account(balance=Money(Decimal("100.00")))
        account.add_income(Money(Decimal("10.00")), "Same")
        repo.save(account)
        
        repo.save(account)
        
        retrieved = repo.get_by_id(account.account_id)
        assert len(retrieved.history) == 1
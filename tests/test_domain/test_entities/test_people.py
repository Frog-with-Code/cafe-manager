import pytest
from datetime import datetime
from decimal import Decimal
from cafe_manager.domain.entities.people import Employee, EmployeeState, Client
from cafe_manager.domain.entities.finance import Money
from cafe_manager.common.exceptions import EmployeeStateError

class TestEmployee:
    def test_employee_initialization(self):
        emp = Employee(name="Alice", employee_id="emp-1")
        assert emp.name == "Alice"
        assert emp.employee_id == "emp-1"
        assert emp._state == EmployeeState.FREE
        assert isinstance(emp.rest_start, datetime)

    def test_can_work_true(self):
        emp = Employee(name="Alice", employee_id="emp-1", state=EmployeeState.FREE)
        assert emp.can_work() is True

    def test_can_work_false(self):
        emp = Employee(name="Alice", employee_id="emp-1", state=EmployeeState.BUSY)
        assert emp.can_work() is False

    def test_work_success(self):
        emp = Employee(name="Alice", employee_id="emp-1")
        emp.work()
        assert emp._state == EmployeeState.BUSY

    def test_work_failure_already_busy(self):
        emp = Employee(name="Alice", employee_id="emp-1", state=EmployeeState.BUSY)
        with pytest.raises(EmployeeStateError):
            emp.work()

    def test_rest_from_busy(self):
        original_rest = datetime(2020, 1, 1)
        emp = Employee(name="Alice", employee_id="emp-1", state=EmployeeState.BUSY, rest_start=original_rest)
        emp.rest()
        assert emp._state == EmployeeState.FREE
        assert emp.rest_start > original_rest

    def test_rest_already_free(self, capsys):
        emp = Employee(name="Alice", employee_id="emp-1", state=EmployeeState.FREE)
        emp.rest()
        captured = capsys.readouterr()
        assert "already resting" in captured.out
        assert emp._state == EmployeeState.FREE

    def test_unknown_state_raises_error(self):
        emp = Employee(name="Alice", employee_id="emp-1")
        emp._state = "invalid_state" # type: ignore
        with pytest.raises(EmployeeStateError):
            emp.rest()


class TestClient:
    def test_client_initialization(self):
        client = Client(client_id="cli-1", name="Bob")
        assert client.client_id == "cli-1"
        assert client.name == "Bob"
        assert client.total_spent == Money(Decimal("0.00"))
        assert client.orders_amount == 0
        assert isinstance(client.registered_at, datetime)

    def test_client_pay_updates_totals(self):
        client = Client(client_id="cli-1", name="Bob")
        payment = Money(Decimal("15.50"))
        
        client.pay(payment)
        assert client.total_spent == Money(Decimal("15.50"))
        assert client.orders_amount == 1
        
        client.pay(Money(Decimal("10.00")))
        assert client.total_spent == Money(Decimal("25.50"))
        assert client.orders_amount == 2

    def test_client_initialization_with_values(self):
        dt = datetime(2023, 5, 5)
        client = Client(
            client_id="cli-2",
            name="Charlie",
            total_spent=Money(Decimal("100.00")),
            orders_amount=5,
            registered_at=dt
        )
        assert client.total_spent == Money(Decimal("100.00"))
        assert client.orders_amount == 5
        assert client.registered_at == dt
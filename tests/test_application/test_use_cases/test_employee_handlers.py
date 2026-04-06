import pytest
from unittest.mock import MagicMock
from cafe_manager.application.use_cases.employee_handlers import (
    EmployeeHireHandler,
    EmployeeFireHandler,
    EmployeeInfoHandler,
)
from cafe_manager.common.exceptions import EmployeeNotFoundError
from cafe_manager.domain.entities.people import Employee
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.application.interfaces import EmployeeRepo


class TestEmployeeHireHandler:
    @pytest.fixture
    def mock_deps(self):
        employee_repo = MagicMock(spec=EmployeeRepo)
        id_generator = MagicMock(spec=IDGeneratingService)
        id_generator.max_attempts = 100

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.employee_repo = employee_repo

        return uow, employee_repo, id_generator

    def test_handle_success(self, mock_deps):
        uow, employee_repo, id_generator = mock_deps
        generated_id = "emp-ABC123"

        id_generator.generate_unique_code.return_value = generated_id
        employee_repo.get_by_id.return_value = None 

        handler = EmployeeHireHandler(uow, id_generator)
        result_id = handler.handle("Alice Smith")

        assert result_id == generated_id
        employee_repo.save.assert_called_once()
        saved_employee = employee_repo.save.call_args[0][0]
        assert isinstance(saved_employee, Employee)
        assert saved_employee.name == "Alice Smith"
        assert saved_employee.employee_id == generated_id

    def test_handle_id_collision_retry(self, mock_deps):
        uow, employee_repo, id_generator = mock_deps

        id_generator.generate_unique_code.side_effect = ["emp-EXIST", "emp-NEW"]
        employee_repo.get_by_id.side_effect = [MagicMock(spec=Employee), None]

        handler = EmployeeHireHandler(uow, id_generator)
        result_id = handler.handle("Bob Jones")

        assert result_id == "emp-NEW"
        assert id_generator.generate_unique_code.call_count == 2


class TestEmployeeFireHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=EmployeeRepo)

    def test_handle_success(self, mock_repo):
        emp_id = "emp-123"
        mock_repo.get_by_id.return_value = MagicMock(spec=Employee)

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.employee_repo = mock_repo

        handler = EmployeeFireHandler(uow)
        handler.handle(emp_id)

        mock_repo.delete_by_id.assert_called_once_with(emp_id)

    def test_handle_employee_not_found(self, mock_repo):
        mock_repo.get_by_id.return_value = None

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.employee_repo = mock_repo

        handler = EmployeeFireHandler(uow)
        with pytest.raises(EmployeeNotFoundError):
            handler.handle("non-existent")


class TestEmployeeInfoHandler:
    @pytest.fixture
    def mock_repo(self):
        return MagicMock(spec=EmployeeRepo)

    def test_handle_returns_employees(self, mock_repo):
        employees = [Employee("Alice", "emp-1"), Employee("Bob", "emp-2")]
        mock_repo.get_all.return_value = employees

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.employee_repo = mock_repo

        handler = EmployeeInfoHandler(uow)
        result = handler.handle()

        assert result == employees
        assert len(result) == 2

    def test_handle_returns_empty_list_when_none(self, mock_repo):
        mock_repo.get_all.return_value = None

        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.employee_repo = mock_repo

        handler = EmployeeInfoHandler(uow)
        result = handler.handle()

        assert result == []

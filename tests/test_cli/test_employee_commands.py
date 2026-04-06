import pytest
from typer.testing import CliRunner
from pathlib import Path
from cafe_manager.cli.employee_commands import app
from cafe_manager.common.exceptions import EmployeeNotFoundError

runner = CliRunner()
PATCH_TARGET = "cafe_manager.cli.employee_commands"


class TestHireCommand:
    def test_hire_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeHireHandler")
        mock_handler.return_value.handle.return_value = "emp-123"
        
        result = runner.invoke(app, ["hire", "--name", "Alice"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("Alice")
        assert "Employee was hired with ID emp-123" in result.stdout

    def test_hire_runtime_error(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeHireHandler")
        mock_handler.return_value.handle.side_effect = RuntimeError("Creation failed")
        
        result = runner.invoke(app, ["hire", "--name", "Alice"])
        
        assert result.exit_code == 1
        assert "Creation failed" in result.stderr

class TestFireCommand:
    def test_fire_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeFireHandler")
        
        result = runner.invoke(app, ["fire", "--id", "emp-123"])
        
        assert result.exit_code == 0
        mock_handler.return_value.handle.assert_called_once_with("emp-123")
        assert "Employee was fired" in result.stdout

    def test_fire_not_found(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeFireHandler")
        mock_handler.return_value.handle.side_effect = EmployeeNotFoundError("No such employee")
        
        result = runner.invoke(app, ["fire", "--id", "invalid-id"])
        
        assert result.exit_code == 1
        assert "No such employee" in result.stderr

class TestInfoCommand:
    def test_info_basic(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeInfoHandler")
        
        mock_emp = mocker.MagicMock()
        mock_emp.name = "Alice"
        mock_emp.employee_id = "emp-1"
        mock_handler.return_value.handle.return_value = [mock_emp]
        
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "employees" in result.stdout
        assert "Alice" in result.stdout
        assert "emp-1" in result.stdout

    def test_info_expanded(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeInfoHandler")
        
        mock_emp = mocker.MagicMock()
        mock_emp.name = "Bob"
        mock_emp.employee_id = "emp-2"
        mock_emp._state = "WORKING"
        mock_emp.rest_start = "None"
        mock_handler.return_value.handle.return_value = [mock_emp]
        
        result = runner.invoke(app, ["info", "--expanded"])
        
        assert result.exit_code == 0
        assert "WORKING" in result.stdout
        assert "None" in result.stdout

class TestCreateAtmosphereCommand:
    def test_create_atmosphere_success(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeCreateAtmosphere")
        mock_handler.return_value.handle.return_value = "Funny joke here"
        
        result = runner.invoke(app, ["create-atmosphere"])
        
        assert result.exit_code == 0
        assert "Employee tells a joke:" in result.stdout
        assert "Funny joke here" in result.stdout

    def test_create_atmosphere_no_employees(self, mocker):
        mock_handler = mocker.patch(f"{PATCH_TARGET}.EmployeeCreateAtmosphere")
        mock_handler.return_value.handle.side_effect = EmployeeNotFoundError("Nobody here")
        
        result = runner.invoke(app, ["create-atmosphere"])
        
        assert result.exit_code == 1
        assert "Nobody here" in result.stderr
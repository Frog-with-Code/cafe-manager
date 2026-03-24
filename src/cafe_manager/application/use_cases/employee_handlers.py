from cafe_manager.common.exceptions import EmployeeNotFoundError
from cafe_manager.domain.entities.people import Employee
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.application.interfaces import EmployeeRepo


class EmployeeHireHandler:
    def __init__(
        self, employee_repo: EmployeeRepo, id_generator: IDGeneratingService
    ) -> None:
        self._employee_repo = employee_repo
        self._id_generator = id_generator

    def handle(self, name: str) -> str:
        while True:
            generated_id = self._id_generator.generate_unique_code(Employee)
            employee = self._employee_repo.get_by_id(generated_id)

            if employee is None:
                break

        new_employee = Employee(name=name, employee_id=generated_id)
        self._employee_repo.save(new_employee)

        return generated_id


class EmployeeFireHandler:
    def __init__(self, employee_repo: EmployeeRepo) -> None:
        self._employee_repo = employee_repo

    def handle(self, employee_id: str) -> None:
        if self._employee_repo.get_by_id(employee_id) is None:
            raise EmployeeNotFoundError(f"Employee with id {employee_id} was not found")

        self._employee_repo.delete_by_id(employee_id)


class EmployeeInfoHandler:
    def __init__(self, employee_repo: EmployeeRepo) -> None:
        self._employee_repo = employee_repo

    def handle(self) -> list[Employee]:
        employees = self._employee_repo.get_all()
        return employees if employees else []

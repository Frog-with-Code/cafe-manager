import random

from cafe_manager.domain.entities.people import Employee
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.application.interfaces import EmployeeRepo
from cafe_manager.common.exceptions import EmployeeNotFoundError


class EmployeeHireHandler:
    def __init__(
        self, employee_repo: EmployeeRepo, id_generator: IDGeneratingService
    ) -> None:
        self._employee_repo = employee_repo
        self._id_generator = id_generator

    def handle(self, name: str) -> str:
        for _ in range(self._id_generator.max_attempts):
            generated_id = self._id_generator.generate_unique_code(Employee)
            employee = self._employee_repo.get_by_id(generated_id)

            if employee is None:
                break
        else:
            raise RuntimeError("Unique code was not generated. Try to use longer code")

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


class EmployeeCreateAtmosphere:
    jokes = [
        """Собирает мама сына сына в школу. Кладет ему хлеб, колбасу и гвозди. 
    - Мама, мама, а зачем мне это? 
    - Ну как же, берешь хлеб, кладешь колбасу и ешь. 
    - А гвозди? 
    - Так вот же они.""",
        """Идет геолог по полю и видит: пасёт мужик овец. Подходит к нему и спрашивает:
    - Скажи мужик, сколько корма уходит на твоих овец в день?
    - На черных или белых?
    - На черных.
    - 2 кг
    - А на белых?
    - 2 кг.
    - А сколько шерсти дают твои овцы в день?
    - Черные или белые?
    - Ну давай белые.
    - 1 кг
    - Ну а черные?
    - 1 кг
    - Что ты мне голову морочишь. И там, и там одно и то же.
    - Так черные мои.
    - Ааа, а белые тогда чьи?
    - Тоже мои.""",
        """Заходит мужик с чемоданом в аэропорт. Охрана просит его открыть чемодан. А он им отвечает: 
    - Я не могу, у меня там бипки.
    - А что такое бипки?
*3 hours later*
Идет мужик по чистилищу, садится, открывает свой чемодан. А в нем бипки.""",
    ]

    def __init__(self, employee_repo: EmployeeRepo) -> None:
        self._employee_repo = employee_repo

    def _get_random_joke(self) -> str:
        return random.choice(self.jokes)

    def handle(self) -> str:
        employee = self._employee_repo.get_most_free()

        if employee is None:
            raise EmployeeNotFoundError("No free employees")

        return self._get_random_joke()

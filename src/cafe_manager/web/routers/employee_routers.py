from fastapi import APIRouter, Depends

from ..dependencies import get_uow
from ..shemas import EmployeeResponse

from cafe_manager.application.use_cases.employee_handlers import (
    EmployeeCreateAtmosphere,
    EmployeeFireHandler,
    EmployeeHireHandler,
    EmployeeInfoHandler,
)
from cafe_manager.application.uow import UnitOfWork

from cafe_manager.infrastructure.factory import get_id_generator

router = APIRouter()


@router.post("/", status_code=201)
def hire_employee(name: str, uow: UnitOfWork = Depends(get_uow)):
    """Hire new employee"""
    id_generator = get_id_generator()
    handler = EmployeeHireHandler(uow=uow, id_generator=id_generator)

    employee_id = handler.handle(name)
    return {
        "status": "success",
        "id": employee_id,
        "message": f"Employee with ID '{employee_id}' was hired'",
    }


@router.delete("/{employee_id}", status_code=200)
def fire_employee(employee_id: str, uow: UnitOfWork = Depends(get_uow)):
    """Fire employee by his ID"""
    handler = EmployeeFireHandler(uow)

    handler.handle(employee_id)
    return {
        "status": "success",
        "message": f"Employee with ID '{employee_id}' was fired",
    }


@router.get("/", response_model=list[EmployeeResponse])
def get_employees_info(uow: UnitOfWork = Depends(get_uow)):
    """Show info about all employees"""
    handler = EmployeeInfoHandler(uow)
    return handler.handle()


@router.get("/atmosphere")
def create_atmosphere(uow: UnitOfWork = Depends(get_uow)):
    """Get a joke from a free employee to create atmosphere"""
    handler = EmployeeCreateAtmosphere(uow)

    joke = handler.handle()
    return {"joke": joke}

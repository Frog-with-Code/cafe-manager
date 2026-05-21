from fastapi import Request
from fastapi.responses import JSONResponse
from cafe_manager.common import exceptions


EXCEPTION_MAP = {
    exceptions.AccountNotFoundError: 404,
    exceptions.CafeEnvNotFoundError: 404,
    exceptions.ChairNotFoundError: 404,
    exceptions.ClientNotFoundError: 404,
    exceptions.CoffeeMachineNotFoundError: 404,
    exceptions.EmployeeNotFoundError: 404,
    exceptions.IngredientNotFoundError: 404,
    exceptions.MenuItemNotFoundError: 404,
    exceptions.OrderNotFoundError: 404,
    exceptions.TableNotFoundError: 404,
    
    exceptions.TableSuitableNotFoundError: 400,
    exceptions.CafeEnvAlreadyInitError: 409,
    exceptions.CafeEnvExistsError: 409,
    exceptions.IngredientExistsError: 409,
    exceptions.MenuItemExistsError: 409,

    exceptions.CafeEnvNameError: 400,
    exceptions.CafeEnvNoActiveError: 400,
    exceptions.ChairShortageError: 400,
    exceptions.ChairStateError: 400,
    exceptions.CoffeeMachineStateError: 400,
    exceptions.InsufficientBudgetError: 400,
    exceptions.InsufficientStocksError: 400,
    exceptions.KitchenOverloadError: 400,
    exceptions.MenuItemRepeatError: 400,
    exceptions.OrderStateError: 400,
    exceptions.TableBusyError: 400,
    exceptions.TablePlacesError: 400,
    exceptions.TableStateError: 400,

    exceptions.IDGeneratingError: 500, 
}


def add_exception_handlers(app):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        
        for exc_class, status_code in EXCEPTION_MAP.items():
            if isinstance(exc, exc_class):
                return JSONResponse(
                    status_code=status_code,
                    content={"detail": str(exc)},
                )
        
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred."},
        )

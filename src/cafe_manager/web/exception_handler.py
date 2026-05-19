from fastapi import Request
from fastapi.responses import JSONResponse
from cafe_manager.common import exceptions as domain_exc

from cafe_manager.common import exceptions as domain_exc

EXCEPTION_MAP = {
    domain_exc.AccountNotFoundError: 404,
    domain_exc.CafeEnvNotFoundError: 404,
    domain_exc.ChairNotFoundError: 404,
    domain_exc.ClientNotFoundError: 404,
    domain_exc.CoffeeMachineNotFoundError: 404,
    domain_exc.EmployeeNotFoundError: 404,
    domain_exc.IngredientNotFoundError: 404,
    domain_exc.MenuItemNotFoundError: 404,
    domain_exc.OrderNotFoundError: 404,
    domain_exc.TableNotFoundError: 404,
    
    domain_exc.TableSuitableNotFoundError: 400,
    domain_exc.CafeEnvAlreadyInitError: 409,
    domain_exc.CafeEnvExistsError: 409,
    domain_exc.IngredientExistsError: 409,
    domain_exc.MenuItemExistsError: 409,

    domain_exc.CafeEnvNameError: 400,
    domain_exc.CafeEnvNoActiveError: 400,
    domain_exc.ChairShortageError: 400,
    domain_exc.ChairStateError: 400,
    domain_exc.CoffeeMachineStateError: 400,
    domain_exc.InsufficientBudgetError: 400,
    domain_exc.InsufficientStocksError: 400,
    domain_exc.KitchenOverloadError: 400,
    domain_exc.MenuItemRepeatError: 400,
    domain_exc.OrderStateError: 400,
    domain_exc.TableBusyError: 400,
    domain_exc.TablePlacesError: 400,
    domain_exc.TableStateError: 400,

    domain_exc.IDGeneratingError: 500, 
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

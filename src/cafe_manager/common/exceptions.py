from click import ClickException
from rich.console import Console
from rich.panel import Panel


class ExpectedError(Exception):
    pass


class TableError(ExpectedError):
    pass


class TableStateError(TableError):
    pass


class TableOccupationError(TableError):
    pass


class TableCleaningError(TableError):
    pass


class TablePlacesError(TableError):
    pass


class ChairError(ExpectedError):
    pass


class ChairStateError(ChairError):
    pass


class CoffeeMachineStateError(ExpectedError):
    pass


class CoffeeMachinePipelineError(CoffeeMachineStateError):
    pass


class FinanceError(ExpectedError):
    pass


class InsufficientBudgetError(FinanceError):
    pass


class IncorrectMoneyAmountError(FinanceError):
    pass


class OrderError(ExpectedError):
    pass


class OrderStateError(OrderError):
    pass


class OrderModificationError(OrderError):
    pass


class OrderCreationError(OrderError):
    pass


class OrderPaymentError(OrderError):
    pass


class EmployeeError(ExpectedError):
    pass


class EmployeeStateError(EmployeeError):
    pass


class InventoryError(ExpectedError):
    pass


class ImpossibleUnloading(InventoryError):
    pass


class MenuError(ExpectedError):
    pass


class RecipeError(MenuError):
    pass


class MenuItemError(MenuError):
    pass


class MenuItemTypeError(MenuItemError):
    pass


class KitchenError(ExpectedError):
    pass


class KitchenWorkError(ExpectedError):
    pass


class KitchenOverloadError(KitchenError):
    pass


class KitchenReadyError(KitchenError):
    pass


class NotFoundError(ExpectedError):
    pass


class CafeError(ExpectedError):
    pass


class CafeEnvError(CafeError):
    pass


class CafeEnvNameError(CafeEnvError):
    pass


class CafeEnvNameSymbolsError(CafeEnvNameError):
    pass


class CafeEnvNameLengthError(CafeEnvNameError):
    pass


class CafeEnvAlreadyInitError(CafeEnvError):
    pass


class CafeEnvExistsError(CafeEnvError):
    pass


class CafeEnvNoActiveError(CafeEnvError):
    pass


class CafeEnvNotFoundError(CafeEnvError):
    pass


class CafeInitError(CafeError):
    pass


class CLIBusinessError(ClickException):
    pass


class CLIUnexpectedError(Exception):
    exit_code = 1

    def __init__(self, message: str, title: str = "Unexpected Error"):
        self.message = message
        self.title = title
        super().__init__(message)

    def show(self, file=None):
        console = Console()

        console.print(
            Panel(
                self.message,
                title=f"{self.title}",
                title_align="left",
                border_style="yellow",
            )
        )
        
class DBError(Exception):
    pass

class RecordNotUpdatedError(DBError):
    pass

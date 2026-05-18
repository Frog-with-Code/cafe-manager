from click import ClickException
from rich.console import Console
from rich.panel import Panel


class TableError(Exception):
    pass


class TableNotFoundError(TableError):
    pass


class TableStateError(TableError):
    pass


class TableSuitableNotFoundError(TableError):
    pass


class TableBusyError(TableError):
    pass


class TablePlacesError(TableError):
    pass


class ChairError(Exception):
    pass


class ChairStateError(ChairError):
    pass


class ChairShortageError(ChairError):
    pass


class ChairNotFoundError(ChairError):
    pass


class CoffeeMachineError(Exception):
    pass


class CoffeeMachineStateError(CoffeeMachineError):
    pass


class CoffeeMachineNotFoundError(CoffeeMachineError):
    pass


class FinanceError(Exception):
    pass


class AccountNotFoundError(FinanceError):
    pass


class InsufficientBudgetError(FinanceError):
    pass


class IncorrectMoneyAmountError(FinanceError):
    pass


class OrderError(Exception):
    pass


class OrderStateError(OrderError):
    pass


class OrderNotFoundError(OrderError):
    pass


class OrderIsEmptyError(OrderError):
    pass


class EmployeeError(Exception):
    pass


class EmployeeNotFoundError(EmployeeError):
    pass


class EmployeeNotAssignedError(EmployeeError):
    pass


class EmployeeStateError(EmployeeError):
    pass


class InventoryError(Exception):
    pass


class InsufficientStocksError(InventoryError):
    pass


class IngredientError(Exception):
    pass


class IngredientExistsError(IngredientError):
    pass


class IngredientNotFoundError(IngredientError):
    pass


class MenuItemError(Exception):
    pass


class MenuItemRepeatError(MenuItemError):
    pass


class MenuItemExistsError(MenuItemError):
    pass


class MenuItemNotFoundError(MenuItemError):
    pass


class KitchenError(Exception):
    pass


class KitchenOverloadError(KitchenError):
    pass


class CafeError(Exception):
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


class CLIBusinessError(ClickException):
    pass


class ClientError(Exception):
    pass

class IDGeneratingError(RuntimeError):
    pass

class ClientNotFoundError(ClientError):
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

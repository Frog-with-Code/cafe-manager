import time
from enum import StrEnum
from rich.progress import track

from cafe_manager.common.exceptions import (
    RecipeError,
    CoffeeMachinePipelineError,
    CoffeeMachineStateError,
    TablePlacesError,
    TableStateError,
    ChairStateError,
)
from .menu import MenuItem


class TableState(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    DIRTY = "dirty"


class CoffeeMachineState(StrEnum):
    IDLE = "idle"
    GRINDING = "grinding"
    BREWING = "brewing"
    STEAMING = "steaming"
    SERVICE_REQUIRED = "service-required"
    IN_SERVICE = "in-service"


class ChairState(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"


class Chair:
    def __init__(
        self,
        chair_id: int | None = None,
        table_id: int | None = None,
        state: ChairState = ChairState.AVAILABLE,
    ) -> None:
        self.chair_id = chair_id
        self._table_id = table_id
        self._state = state

    def can_be_reserved(self) -> bool:
        return self._state == ChairState.AVAILABLE

    def reserve(self) -> None:
        if not self.can_be_reserved():
            raise ChairStateError("Chair is not available")

        self._state = ChairState.RESERVED

    def occupy(self) -> None:
        if self._state != ChairState.RESERVED:
            raise ChairStateError("Chair is not reserved")

        self._state = ChairState.RESERVED

    def free(self) -> None:
        self._state = ChairState.AVAILABLE

    def assign_to_table(self, table_id: int | None) -> None:
        if not isinstance(table_id, int):
            raise ValueError("Incorrect id type")
        self._table_id = table_id


class Table:
    def __init__(
        self,
        max_places: int,
        state: TableState = TableState.AVAILABLE,
        table_id: int | None = None,
        chairs_ids: set[int] | None = None,
    ) -> None:
        self.table_id = table_id
        self.max_places = max_places
        self._state = state
        self._chairs_ids = chairs_ids or set()

    def clean(self) -> None:
        match (self._state):
            case TableState.OCCUPIED | TableState.RESERVED:
                raise TableStateError("Impossible to clean reserved/occupied table")
            case TableState.DIRTY:
                self._state = TableState.AVAILABLE
            case _:
                raise TableStateError("Unknown state")

    @property
    def chairs_ids(self) -> set[int]:
        return self._chairs_ids.copy()

    @property
    def chairs_amount(self) -> int:
        return len(self._chairs_ids)

    @property
    def is_available(self) -> bool:
        return self._state == TableState.AVAILABLE

    def can_be_reserved(self, people_amount: int) -> bool:
        return (
            self._state == TableState.AVAILABLE
            and len(self._chairs_ids) >= people_amount
        )

    def reserve(self, people_amount: int) -> None:
        if not self.can_be_reserved(people_amount):
            raise TableStateError(
                "Impossible to reserve table. It's not available or don't match the conditions"
            )
        self._state = TableState.RESERVED

    def occupy(self) -> None:
        if self._state != TableState.RESERVED:
            raise TableStateError("Impossible to occupy not reserved table")

        self._state = TableState.OCCUPIED

    def free(self) -> None:
        if self._state in (
            TableState.AVAILABLE,
            TableState.RESERVED,
            TableState.OCCUPIED,
        ):
            self._state = TableState.AVAILABLE

    def add_chair(self, chair_id: int | None) -> None:
        if not isinstance(chair_id, int):
            raise ValueError("Incorrect id type")
        if self.chairs_amount >= self.max_places:
            raise TablePlacesError("Max places amount was already achieved")

        self._chairs_ids.add(chair_id)

    def remove_chair(self, chair_id: int | None) -> None:
        if not isinstance(chair_id, int):
            raise ValueError("Incorrect id type")
        try:
            self._chairs_ids.remove(chair_id)
        except KeyError:
            raise TablePlacesError(
                f"Chair with id {chair_id} not assigned to table {self.table_id}"
            )


class CoffeeMachine:
    PROGRESS_STEPS = 5
    PROGRESS_TOTAL = 100
    GRINDING_TIME = 5
    BREWING_TIME = 5
    STEAMING_TIME = 5

    def __init__(
        self,
        model: str,
        machine_id: int | None = None,
        maintenance_limit: int = 200,
        cycles_count: int = 0,
        state: CoffeeMachineState = CoffeeMachineState.IDLE,
    ) -> None:
        self.machine_id = machine_id
        self.model = model
        self.maintenance_limit = maintenance_limit
        self.cycles_count = cycles_count
        self._state = state

    def _grind(self) -> None:
        if self._state != CoffeeMachineState.IDLE:
            raise CoffeeMachinePipelineError(
                "Impossible to start grinding process. Coffee-machine is not ready to use"
            )

        self._state = CoffeeMachineState.GRINDING
        for _ in track(
            range(0, self.PROGRESS_TOTAL, self.PROGRESS_TOTAL // self.PROGRESS_STEPS),
            description="Grinding...",
        ):
            time.sleep(self.GRINDING_TIME / self.PROGRESS_STEPS)

    def _brew(self) -> None:
        if self._state != CoffeeMachineState.GRINDING:
            raise CoffeeMachinePipelineError(
                "Impossible to start brewing process. Coffee beans were not grinded"
            )

        self._state = CoffeeMachineState.BREWING
        for _ in track(
            range(0, self.PROGRESS_TOTAL, self.PROGRESS_TOTAL // self.PROGRESS_STEPS),
            description="Brewing...",
        ):
            time.sleep(self.BREWING_TIME // self.PROGRESS_STEPS)

    def _steam(self) -> None:
        if self._state != CoffeeMachineState.BREWING:
            raise CoffeeMachinePipelineError(
                "Impossible to start steaming process. Coffee was not brewed"
            )

        self._state = CoffeeMachineState.STEAMING
        for _ in track(
            range(0, self.PROGRESS_TOTAL, self.PROGRESS_TOTAL // self.PROGRESS_STEPS),
            description="Steaming...",
        ):
            time.sleep(self.STEAMING_TIME / self.PROGRESS_STEPS)

    def service(self) -> None:
        match (self._state):
            case CoffeeMachineState.SERVICE_REQUIRED:
                self._state = CoffeeMachineState.IN_SERVICE
                self.cycles_count = 0
            case (
                CoffeeMachineState.GRINDING
                | CoffeeMachineState.BREWING
                | CoffeeMachineState.STEAMING
                | CoffeeMachineState.IN_SERVICE
            ):
                raise CoffeeMachineStateError(
                    "Impossible to carry out maintenance during working process"
                )
            case _:
                raise CoffeeMachineStateError("UnknownState")

    def resume(self) -> None:
        if self._state == CoffeeMachineState.IN_SERVICE:
            self._state = CoffeeMachineState.IDLE

        raise CoffeeMachineStateError(
            "Impossible to resume work of coffee-machine, which is not in service"
        )

    def make_coffee(self, coffee: MenuItem) -> None:
        if self._state != CoffeeMachineState.IDLE:
            raise CoffeeMachineStateError("Coffee-machine is not ready to use")
        if not coffee.requires_coffee_machine:
            raise RecipeError("No coffee-machine needed")
        self._grind()
        self._brew()
        if coffee.requires_milk_foam:
            self._steam()

        self._state = CoffeeMachineState.IDLE
        self.cycles_count += 1

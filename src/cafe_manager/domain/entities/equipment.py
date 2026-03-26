from enum import StrEnum

from cafe_manager.common.exceptions import (
    CoffeeMachineStateError,
    TablePlacesError,
    TableStateError,
    ChairStateError,
)


class TableState(StrEnum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    DIRTY = "dirty"


class CoffeeMachineState(StrEnum):
    IDLE = "idle"
    WORKING = "working"
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

    def reserve(self) -> None:
        if self._state != ChairState.AVAILABLE:
            raise ChairStateError(
                "Impossible to reserve. Chair is not available to use"
            )

        self._state = ChairState.RESERVED

    def occupy(self) -> None:
        if self._state != ChairState.RESERVED:
            raise ChairStateError("Chair is not reserved")

        self._state = ChairState.RESERVED

    def free(self) -> None:
        self._state = ChairState.AVAILABLE

    def assign_to_table(self, table_id: int | None) -> None:
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
        if self._state in (TableState.RESERVED, TableState.OCCUPIED):
            raise TableStateError("Impossible to clean reserved/occupied table")

        self._state = TableState.AVAILABLE

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
    def __init__(
        self,
        model: str,
        machine_id: int | None = None,
        maintenance_limit: int = 200,
        cycles_count: int = 0,
        state: CoffeeMachineState = CoffeeMachineState.IDLE,
    ) -> None:
        self.model = model

        self.machine_id = machine_id
        self.maintenance_limit = maintenance_limit
        self.cycles_count = cycles_count
        self._state = state

    def service(self) -> None:
        match (self._state):
            case CoffeeMachineState.SERVICE_REQUIRED:
                self._state = CoffeeMachineState.IN_SERVICE
                self.cycles_count = 0
            case CoffeeMachineState.WORKING | CoffeeMachineState.IN_SERVICE:
                raise CoffeeMachineStateError(
                    "Impossible to carry out maintenance during working process"
                )
            case CoffeeMachineState.IDLE:
                raise CoffeeMachineStateError("No need to carry out maintenance")

    def resume(self) -> None:
        if self._state != CoffeeMachineState.IN_SERVICE:
            raise CoffeeMachineStateError(
                "Impossible to resume work of coffee-machine, which is not in service"
            )
        self._state = CoffeeMachineState.IDLE

    def start(self) -> None:
        if self._state != CoffeeMachineState.IDLE:
            raise CoffeeMachineStateError("Coffee-machine is not ready to use")

        self._state = CoffeeMachineState.WORKING
        self.cycles_count += 1

    def stop(self) -> None:
        if self._state != CoffeeMachineState.WORKING:
            raise CoffeeMachineStateError("Coffee-machine is not working")

        if self.cycles_count >= self.maintenance_limit:
            self._state = CoffeeMachineState.SERVICE_REQUIRED
        else:
            self._state = CoffeeMachineState.IDLE

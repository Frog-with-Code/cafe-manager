import pytest
from cafe_manager.domain.entities.equipment import (
    Chair, ChairState, Table, TableState, CoffeeMachine, CoffeeMachineState
)
from cafe_manager.common.exceptions import (
    ChairStateError, TableStateError, TablePlacesError, CoffeeMachineStateError
)

class TestChair:
    def test_chair_initialization(self):
        chair = Chair(chair_id=1)
        assert chair.chair_id == 1
        assert chair._state == ChairState.AVAILABLE
        assert chair._table_id is None

    def test_chair_reserve_success(self):
        chair = Chair()
        chair.reserve()
        assert chair._state == ChairState.RESERVED

    def test_chair_reserve_failure(self):
        chair = Chair(state=ChairState.RESERVED)
        with pytest.raises(ChairStateError):
            chair.reserve()

    def test_chair_occupy_success(self):
        chair = Chair(state=ChairState.RESERVED)
        chair.occupy()
        assert chair._state == ChairState.RESERVED

    def test_chair_occupy_failure(self):
        chair = Chair(state=ChairState.AVAILABLE)
        with pytest.raises(ChairStateError):
            chair.occupy()

    def test_chair_free(self):
        chair = Chair(state=ChairState.RESERVED)
        chair.free()
        assert chair._state == ChairState.AVAILABLE

    def test_chair_assign_to_table(self):
        chair = Chair()
        chair.assign_to_table(10)
        assert chair._table_id == 10


class TestTable:
    def test_table_initialization(self):
        table = Table(table_id=1, max_places=4)
        assert table.max_places == 4
        assert table._state == TableState.AVAILABLE
        assert len(table.chairs_ids) == 0

    def test_table_clean_success(self):
        table = Table(max_places=2, state=TableState.DIRTY)
        table.clean()
        assert table._state == TableState.AVAILABLE

    def test_table_clean_failure(self):
        table = Table(max_places=2, state=TableState.OCCUPIED)
        with pytest.raises(TableStateError):
            table.clean()

    def test_table_reserve_success(self):
        table = Table(max_places=4, chairs_ids={1, 2})
        table.reserve(people_amount=2)
        assert table._state == TableState.RESERVED

    def test_table_reserve_insufficient_chairs(self):
        table = Table(max_places=4, chairs_ids={1})
        with pytest.raises(TableStateError):
            table.reserve(people_amount=2)

    def test_table_occupy_success(self):
        table = Table(max_places=2, state=TableState.RESERVED)
        table.occupy()
        assert table._state == TableState.OCCUPIED

    def test_table_occupy_failure(self):
        table = Table(max_places=2, state=TableState.AVAILABLE)
        with pytest.raises(TableStateError):
            table.occupy()

    def test_table_add_chair_success(self):
        table = Table(max_places=2)
        table.add_chair(1)
        assert 1 in table.chairs_ids
        assert table.chairs_amount == 1

    def test_table_add_chair_over_limit(self):
        table = Table(max_places=1, chairs_ids={1})
        with pytest.raises(TablePlacesError):
            table.add_chair(2)

    def test_table_remove_chair_success(self):
        table = Table(max_places=4, chairs_ids={1, 2}, table_id=5)
        table.remove_chair(1)
        assert 1 not in table.chairs_ids
        assert table.chairs_amount == 1

    def test_table_remove_chair_missing(self):
        table = Table(max_places=4, chairs_ids={1}, table_id=5)
        with pytest.raises(TablePlacesError):
            table.remove_chair(99)


class TestCoffeeMachine:
    def test_machine_initialization(self):
        machine = CoffeeMachine(model="X-1", maintenance_limit=10)
        assert machine.model == "X-1"
        assert machine.cycles_count == 0
        assert machine._state == CoffeeMachineState.IDLE

    def test_machine_start_success(self):
        machine = CoffeeMachine(model="X-1")
        machine.start()
        assert machine._state == CoffeeMachineState.WORKING
        assert machine.cycles_count == 1

    def test_machine_start_failure(self):
        machine = CoffeeMachine(model="X-1", state=CoffeeMachineState.WORKING)
        with pytest.raises(CoffeeMachineStateError):
            machine.start()

    def test_machine_service_success(self):
        machine = CoffeeMachine(model="X-1", state=CoffeeMachineState.SERVICE_REQUIRED, cycles_count=50)
        machine.service()
        assert machine._state == CoffeeMachineState.IN_SERVICE
        assert machine.cycles_count == 0

    def test_machine_service_failure_idle(self):
        machine = CoffeeMachine(model="X-1", state=CoffeeMachineState.IDLE)
        with pytest.raises(CoffeeMachineStateError):
            machine.service()

    def test_machine_resume_success(self):
        machine = CoffeeMachine(model="X-1", state=CoffeeMachineState.IN_SERVICE)
        machine.resume()
        assert machine._state == CoffeeMachineState.IDLE

    def test_machine_resume_failure(self):
        machine = CoffeeMachine(model="X-1", state=CoffeeMachineState.WORKING)
        with pytest.raises(CoffeeMachineStateError):
            machine.resume()
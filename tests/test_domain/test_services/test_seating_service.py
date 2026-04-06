import pytest
from cafe_manager.domain.services.seating_service import SeatingService
from cafe_manager.domain.entities.equipment import Table, Chair, TableState, ChairState
from cafe_manager.common.exceptions import ChairShortageError, TableSuitableNotFoundError

class TestSeatingService:
    @pytest.fixture
    def service(self):
        return SeatingService()

    def test_reserve_direct_success(self, service):
        table = Table(table_id=1, max_places=4, chairs_ids={10, 11, 12, 13})
        chair1 = Chair(chair_id=10, table_id=1)
        chair2 = Chair(chair_id=11, table_id=1)
        chair3 = Chair(chair_id=12, table_id=1)
        chair4 = Chair(chair_id=13, table_id=1)
        
        tables = [table]
        free_chairs = [chair1, chair2, chair3, chair4]
        
        reserved_table, modified_tables, reserved_chairs = service.reserve(tables, free_chairs, 2)
        
        assert reserved_table.table_id == 1
        assert reserved_table._state == TableState.RESERVED
        assert len(reserved_chairs) == 2
        assert all(c._state == ChairState.RESERVED for c in reserved_chairs)

    def test_reserve_with_dislocation(self, service):
        source_table = Table(table_id=1, max_places=4, chairs_ids={10})
        target_table = Table(table_id=2, max_places=4, chairs_ids={20, 21})
        
        chair10 = Chair(chair_id=10, table_id=1)
        chair20 = Chair(chair_id=20, table_id=2)
        chair21 = Chair(chair_id=21, table_id=2)
        
        tables = [target_table, source_table]
        free_chairs = [chair10, chair20, chair21]
        
        reserved_table, modified_tables, reserved_chairs = service.reserve(tables, free_chairs, 3)
        
        assert reserved_table.table_id == 2
        assert 20 in target_table.chairs_ids
        assert 21 in target_table.chairs_ids
        assert 20 not in source_table.chairs_ids
        assert chair20._table_id == 2
        assert len(reserved_chairs) == 3

    def test_reserve_smallest_suitable_table(self, service):
        big_table = Table(table_id=1, max_places=10, chairs_ids=set(range(10)))
        small_table = Table(table_id=2, max_places=4, chairs_ids={20, 21, 22, 23})
        
        chairs = [Chair(chair_id=i, table_id=1) for i in range(10)]
        chairs.extend([Chair(chair_id=i, table_id=2) for i in range(20, 24)])
        
        reserved_table, _, _ = service.reserve([big_table, small_table], chairs, 2)
        
        assert reserved_table.table_id == 2

    def test_reserve_no_available_tables(self, service):
        table = Table(table_id=1, max_places=4, state=TableState.OCCUPIED)
        with pytest.raises(TableSuitableNotFoundError):
            service.reserve([table], [], 2)

    def test_reserve_table_too_small(self, service):
        table = Table(table_id=1, max_places=2, chairs_ids={1, 2})
        chair1 = Chair(chair_id=1, table_id=1)
        chair2 = Chair(chair_id=2, table_id=1)
        
        with pytest.raises(TableSuitableNotFoundError):
            service.reserve([table], [chair1, chair2], 4)

    def test_reserve_not_enough_total_chairs(self, service):
        table = Table(table_id=1, max_places=10, chairs_ids={1})
        chair1 = Chair(chair_id=1, table_id=1)
        chair_free = Chair(chair_id=2, table_id=None)
        
        with pytest.raises(TableSuitableNotFoundError):
            service.reserve([table], [chair1, chair_free], 5)

    def test_dislocate_chairs_from_none_table(self, service):
        target_table = Table(table_id=1, max_places=4, chairs_ids=set())
        lonely_chair = Chair(chair_id=99, table_id=None)
        
        tables = [target_table]
        free_chairs = [lonely_chair]
        
        service.reserve(tables, free_chairs, 1)
        
        assert lonely_chair._table_id == 1
        assert 99 in target_table.chairs_ids

    def test_find_suitable_tables_filtering(self, service):
        t1 = Table(table_id=1, max_places=4, state=TableState.AVAILABLE)
        t2 = Table(table_id=2, max_places=2, state=TableState.AVAILABLE)
        t3 = Table(table_id=3, max_places=4, state=TableState.RESERVED)
        
        suitable = service._find_suitable_tables([t1, t2, t3], 3)
        
        assert len(suitable) == 1
        assert suitable[0].table_id == 1
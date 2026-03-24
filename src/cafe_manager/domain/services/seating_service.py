from cafe_manager.common.exceptions import (
    ChairShortageError,
    TableSuitableNotFoundError,
)
from cafe_manager.domain.entities.equipment import Table, Chair
from cafe_manager.common.utils import validate_non_negative


class SeatingService:
    def _find_suitable_tables(
        self, free_tables: list[Table], people_amount: int
    ) -> list[Table]:
        return [
            table
            for table in free_tables
            if table.is_available and table.max_places >= people_amount
        ]

    def _move_chair(
        self, chair: Chair, last_table: Table | None, target_table: Table
    ) -> None:
        if last_table:
            last_table.remove_chair(chair.chair_id)
        chair.assign_to_table(target_table.table_id)
        target_table.add_chair(chair.chair_id)

    def _get_table_by_id(
        self, tables: list[Table], table_id: int | None
    ) -> Table | None:
        if table_id is None:
            return None
        return next((table for table in tables if table.table_id == table_id), None)

    def _get_chair_by_id(self, chairs: list[Chair], chair_id: int) -> Chair:
        return next((chair for chair in chairs if chair.chair_id == chair_id))

    def _dislocate_chairs(
        self,
        free_chairs: list[Chair],
        tables: list[Table],
        target_table: Table,
        people_amount: int,
    ) -> list[Table]:
        required_amount = people_amount - target_table.chairs_amount

        if required_amount <= 0:
            return []

        chairs_to_move = [
            chair
            for chair in free_chairs
            if chair.chair_id not in target_table.chairs_ids
        ]

        if len(chairs_to_move) < required_amount:
            raise ChairShortageError("Not enough free chairs to fill the table")

        modified_tables = []
        for chair in chairs_to_move[:required_amount]:
            last_table = self._get_table_by_id(tables, chair._table_id)
            self._move_chair(chair, last_table, target_table)
            if last_table:
                modified_tables.append(last_table)

        return modified_tables

    def _get_available_tables(self, tables: list[Table]) -> list[Table]:
        available = [t for t in tables if t.is_available]
        if not available:
            raise TableSuitableNotFoundError("No free tables")
        return available

    def _select_reservation_target(
        self,
        available_tables: list[Table],
        free_chairs: list[Chair],
        people_amount: int,
    ) -> tuple[Table, bool]:
        direct_candidates = [
            t for t in available_tables if t.can_be_reserved(people_amount)
        ]
        need_chair_dislocation = False

        if direct_candidates:
            best_table = min(direct_candidates, key=lambda t: t.max_places)
            return best_table, need_chair_dislocation

        suitable_candidates = self._find_suitable_tables(
            available_tables, people_amount
        )

        if not suitable_candidates:
            raise TableSuitableNotFoundError(
                f"No available table for {people_amount} people"
            )

        best_table = max(suitable_candidates, key=lambda t: t.chairs_amount)

        total_capacity = len(free_chairs) + best_table.chairs_amount
        if people_amount > total_capacity:
            raise TableSuitableNotFoundError(
                f"Not enough chairs for {people_amount} people"
            )

        need_chair_dislocation = True
        return best_table, need_chair_dislocation

    def _proceed_reservation(
        self, table: Table, chairs: list[Chair], people_amount: int
    ) -> tuple[Table, list[Chair]]:
        table.reserve(people_amount)

        chairs_to_occupy_ids = list(table.chairs_ids)[:people_amount]

        occupied_chairs = []
        for chair_id in chairs_to_occupy_ids:
            chair = self._get_chair_by_id(chairs, chair_id)
            chair.reserve()
            occupied_chairs.append(chair)

        return table, occupied_chairs

    def reserve(
        self,
        tables: list[Table],
        free_chairs: list[Chair],
        people_amount: int,
    ) -> tuple[Table, list[Table], list[Chair]]:
        validate_non_negative(people_amount)
        available_tables = self._get_available_tables(tables)

        modified_tables = []

        best_table, need_chair_dislocation = self._select_reservation_target(
            available_tables, free_chairs, people_amount
        )

        if need_chair_dislocation:
            modified_tables = self._dislocate_chairs(
                free_chairs, tables, best_table, people_amount
            )

        reserved_table, reserved_chairs = self._proceed_reservation(
            best_table, free_chairs, people_amount
        )
        modified_tables.append(reserved_table)

        return reserved_table, modified_tables, reserved_chairs

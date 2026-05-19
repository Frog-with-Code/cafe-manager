import random

from cafe_manager.common.exceptions import IDGeneratingError
from cafe_manager.domain.repository import OuterIDRepo
from cafe_manager.domain.services.interfaces import IDGenerator


class RandomIDGenerator(IDGenerator):
    prefix_map = {"Client": "cli", "Employee": "emp", "Order": "ord"}

    def __init__(self, max_attempts: int = 100) -> None:
        self.max_attempts = max_attempts

    def _get_prefix(self, obj_class: type) -> str:
        name = obj_class.__name__
        default_len = 3 if len(name) > 3 else len(name)
        return self.prefix_map.get(name, name[:default_len])

    def _generate_code(self, length) -> str:
        characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(random.choices(characters, k=length))

    def _is_unique(self, generated_id: str, repo: OuterIDRepo) -> bool:
        entity = repo.get_by_id(generated_id)

        return entity is None

    def generate_unique_code(
        self, obj_class: type, repo: OuterIDRepo, length: int = 6
    ) -> str | None:
        for _ in range(self.max_attempts):
            generated_id = (
                self._get_prefix(obj_class) + "-" + self._generate_code(length)
            )
            if self._is_unique(generated_id, repo):
                return generated_id

        raise IDGeneratingError("Unique code was not generated. Try to use longer code")

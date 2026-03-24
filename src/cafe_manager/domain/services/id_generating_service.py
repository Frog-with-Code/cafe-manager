import random


class IDGeneratingService:
    prefix_map = {"Client": "cli", "Employee": "emp", "Order": "ord"}

    def __init__(self) -> None:
        self.attempts = 0

    def _get_prefix(self, obj_class: type) -> str:
        name = obj_class.__name__
        default_len = 3 if len(name) > 3 else len(name)
        return self.prefix_map.get(name, name[:default_len])

    def _generate_code(self, length) -> str:
        characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(random.choices(characters, k=length))

    def generate_unique_code(self, obj_class: type, max_attempts: int = 100, length: int = 6) -> str:
        self.attempts += 1
        if self.attempts > max_attempts:
            raise RuntimeError("Unique code was not generated. Try to use longer code")

        return self._get_prefix(obj_class) + "-" + self._generate_code(length)

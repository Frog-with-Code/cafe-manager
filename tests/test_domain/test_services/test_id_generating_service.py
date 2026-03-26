import pytest
from cafe_manager.domain.services.id_generating_service import IDGeneratingService
from cafe_manager.domain.entities.people import Client, Employee
from cafe_manager.domain.entities.order import Order

class TestIDGeneratingService:
    @pytest.fixture
    def service(self):
        return IDGeneratingService()

    def test_get_prefix_known_classes(self, service):
        assert service._get_prefix(Client) == "cli"
        assert service._get_prefix(Employee) == "emp"
        assert service._get_prefix(Order) == "ord"

    def test_get_prefix_unknown_class(self, service):
        class UnknownEntity: pass
        class XYZ: pass
        assert service._get_prefix(UnknownEntity) == "Unk"
        assert service._get_prefix(XYZ) == "XYZ"

    def test_generate_code_format(self, service):
        code = service.generate_unique_code(Client, length=6)
        prefix, random_part = code.split("-")
        assert prefix == "cli"
        assert len(random_part) == 6

    def test_generate_code_custom_params(self, service):
        code = service.generate_unique_code(Order, length=12)
        assert len(code) == 16 # "ord" + "-" + 12 chars
        assert code.startswith("ord-")

    def test_attempts_incrementation(self, service):
        assert service.attempts == 0
        service.generate_unique_code(Employee)
        assert service.attempts == 1
        service.generate_unique_code(Employee)
        assert service.attempts == 2

    def test_allowed_characters_only(self, service):
        allowed = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = service.generate_unique_code(Client, length=100)
        random_part = code.split("-")[1]
        assert all(char in allowed for char in random_part)

    def test_uniqueness_basic(self, service):
        codes = {service.generate_unique_code(Client) for _ in range(100)}
        assert len(codes) == 100
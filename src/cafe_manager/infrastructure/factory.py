from pathlib import Path

from .db.sqlite.uow import SQLiteUnitOfWork
from .env_manager import EnvironmentManager
from .services.id_generator import RandomIDGenerator

from cafe_manager.domain.repository import OuterIDRepo
from cafe_manager.domain.services.ingredient_calculator import DefaultIngredientCalculator
from cafe_manager.domain.services.interfaces import IDGenerator, IngredientCalculator, PaymentService, SeatingService
from cafe_manager.domain.services.payment_service import DefaultPaymentService
from cafe_manager.domain.services.seating_service import DefaultSeatingService

from cafe_manager.application.uow import UnitOfWork

def create_uow(env_path: Path) -> UnitOfWork:
    return SQLiteUnitOfWork(env_path)

def get_active_path() -> Path:
    env_manager = EnvironmentManager()
    active_env = env_manager.get_active_env_path()
    if active_env is None:
        raise RuntimeError("No active cafe environment")
    return active_env

def get_id_generator(max_attempts: int = 100) -> IDGenerator:
    return RandomIDGenerator(max_attempts)

def get_ingredient_calculator() -> IngredientCalculator:
    return DefaultIngredientCalculator()

def get_payment_service() -> PaymentService:
    return DefaultPaymentService()

def get_seating_service() -> SeatingService:
    return DefaultSeatingService()
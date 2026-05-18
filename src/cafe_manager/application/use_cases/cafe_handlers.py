import re
from pathlib import Path

from cafe_manager.domain.entities.cafe import Cafe
from cafe_manager.domain.entities.finance import Money, Account
from cafe_manager.application.uow import UnitOfWork
from cafe_manager.infrastructure.env_manager import EnvironmentManager

from cafe_manager.common.exceptions import (
    CafeEnvAlreadyInitError,
    CafeEnvExistsError,
    CafeEnvNameLengthError,
    CafeEnvNameSymbolsError,
    CafeEnvNoActiveError,
    CafeEnvNotFoundError,
)


class CafeCreateHandler:
    def __init__(self, env_folder_path: Path, env_manager: EnvironmentManager) -> None:
        self.base_path = env_folder_path
        self._env_manager = env_manager

    def handle(self, name: str) -> None:
        if len(name) > 25:
            raise CafeEnvNameLengthError("Provided name is too long")

        pattern = r"^[a-zA-Z0-9_\-]+$"
        if not re.match(pattern, name):
            raise CafeEnvNameSymbolsError(
                "Provided name contains forbidden symbols. Only latin letters, digits, tie and underscore are allowed"
            )

        try:
            self._env_manager.create_env(name)
        except FileExistsError:
            raise CafeEnvExistsError(
                f"Impossible to create cafe '{name}'. Such cafe already exists"
            )


class CafeRemoveHandler:
    def __init__(self, env_manager: EnvironmentManager) -> None:
        self._env_manager = env_manager

    def handle(self, name: str) -> None:
        try:
            self._env_manager.remove_env(name)
        except FileNotFoundError:
            raise CafeEnvNotFoundError(
                f"Impossible to remove cafe '{name}'. It doesn't exist"
            )


class CafeActivateHandler:
    def __init__(self, env_folder_path: Path, env_manager: EnvironmentManager) -> None:
        self.base_path = env_folder_path
        self._env_manager = env_manager

    def handle(self, name: str) -> None:
        db_path = self.base_path / f"{name}.db"

        if not db_path.exists():
            raise CafeEnvNotFoundError(
                f"Impossible to activate environment '{name}'. It doesn't exist"
            )

        self._env_manager.activate_env(db_path)


class CafeDeactivateHandler:
    def __init__(self, env_manager: EnvironmentManager) -> None:
        self._env_manager = env_manager

    def handle(self) -> None:
        try:
            self._env_manager.deactivate_env()
        except FileNotFoundError:
            raise CafeEnvNoActiveError(
                "Impossible to deactivate. No active environments"
            )


class CafeInitHandler:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def handle(self, name: str, address: str, startup_capital: Money) -> None:
        with self._uow as uow:
            if uow.cafe_repo.get() or uow.finance_repo.get_primary():
                raise CafeEnvAlreadyInitError(
                    "You can have only 1 cafe in the environment. Try to switch to another environment with not initialized cafe"
                )

            cafe = Cafe(name, address)
            account = Account(balance=startup_capital)

            uow.cafe_repo.save(cafe)
            uow.finance_repo.save(account)
            uow.finance_repo.set_primary(account.account_id)
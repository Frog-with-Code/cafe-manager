import pytest
from pathlib import Path
from unittest.mock import MagicMock
from cafe_manager.application.use_cases.cafe_handlers import (
    CafeCreateHandler,
    CafeRemoveHandler,
    CafeActivateHandler,
    CafeDeactivateHandler,
    CafeInitHandler,
)
from cafe_manager.common.exceptions import (
    CafeEnvExistsError,
    CafeEnvNameLengthError,
    CafeEnvNameSymbolsError,
    CafeEnvNoActiveError,
    CafeEnvNotFoundError,
    CafeEnvAlreadyInitError,
)
from cafe_manager.domain.entities.finance import Money

class TestCafeCreateHandler:
    @pytest.fixture
    def mock_env_manager(self):
        return MagicMock()

    def test_handle_success(self, tmp_path, mock_env_manager):
        handler = CafeCreateHandler(tmp_path, mock_env_manager)
        handler.handle("valid-cafe")
        mock_env_manager.create_env.assert_called_once_with("valid-cafe")

    def test_handle_name_too_long(self, tmp_path, mock_env_manager):
        handler = CafeCreateHandler(tmp_path, mock_env_manager)
        with pytest.raises(CafeEnvNameLengthError):
            handler.handle("a" * 26)

    def test_handle_invalid_symbols(self, tmp_path, mock_env_manager):
        handler = CafeCreateHandler(tmp_path, mock_env_manager)
        for name in ["cafe name", "cafe!", "@cafe"]:
            with pytest.raises(CafeEnvNameSymbolsError):
                handler.handle(name)

    def test_handle_already_exists(self, tmp_path, mock_env_manager):
        mock_env_manager.create_env.side_effect = FileExistsError
        handler = CafeCreateHandler(tmp_path, mock_env_manager)
        with pytest.raises(CafeEnvExistsError):
            handler.handle("existing")


class TestCafeRemoveHandler:
    @pytest.fixture
    def mock_env_manager(self):
        return MagicMock()

    def test_handle_success(self, mock_env_manager):
        handler = CafeRemoveHandler(mock_env_manager)
        handler.handle("to_remove")
        mock_env_manager.remove_env.assert_called_once_with("to_remove")

    def test_handle_not_found(self, mock_env_manager):
        mock_env_manager.remove_env.side_effect = FileNotFoundError
        handler = CafeRemoveHandler(mock_env_manager)
        with pytest.raises(CafeEnvNotFoundError):
            handler.handle("ghost")


class TestCafeActivateHandler:
    @pytest.fixture
    def mock_env_manager(self):
        return MagicMock()

    def test_handle_success(self, tmp_path, mock_env_manager):
        db_path = tmp_path / "target.db"
        db_path.touch()
        handler = CafeActivateHandler(tmp_path, mock_env_manager)
        
        handler.handle("target")
        mock_env_manager.activate_env.assert_called_once_with(db_path)

    def test_handle_not_found(self, tmp_path, mock_env_manager):
        handler = CafeActivateHandler(tmp_path, mock_env_manager)
        with pytest.raises(CafeEnvNotFoundError):
            handler.handle("missing")


class TestCafeDeactivateHandler:
    @pytest.fixture
    def mock_env_manager(self):
        return MagicMock()

    def test_handle_success(self, mock_env_manager):
        handler = CafeDeactivateHandler(mock_env_manager)
        handler.handle()
        mock_env_manager.deactivate_env.assert_called_once()

    def test_handle_no_active_env(self, mock_env_manager):
        mock_env_manager.deactivate_env.side_effect = FileNotFoundError
        handler = CafeDeactivateHandler(mock_env_manager)
        with pytest.raises(CafeEnvNoActiveError):
            handler.handle()


class TestCafeInitHandler:
    @pytest.fixture
    def mock_uow(self):
        uow = MagicMock()
        uow.__enter__.return_value = uow
        uow.cafe_repo = MagicMock()
        uow.finance_repo = MagicMock()
        return uow

    def test_handle_success(self, mock_uow):
        mock_uow.cafe_repo.get.return_value = None
        mock_uow.finance_repo.get_primary.return_value = None
        
        handler = CafeInitHandler(mock_uow)
        handler.handle("My Cafe", "Street 1", Money.from_any(500))
        
        mock_uow.cafe_repo.save.assert_called_once()
        mock_uow.finance_repo.save.assert_called_once()
        mock_uow.finance_repo.set_primary.assert_called_once()

    def test_handle_already_initialized(self, mock_uow):
        mock_uow.cafe_repo.get.return_value = MagicMock()
        handler = CafeInitHandler(mock_uow)
        with pytest.raises(CafeEnvAlreadyInitError):
            handler.handle("Cafe", "Addr", Money.from_any(0))
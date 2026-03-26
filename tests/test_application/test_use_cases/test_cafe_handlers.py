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
        handler.handle("valid-cafe-123")
        expected_path = tmp_path / "valid-cafe-123.db"
        mock_env_manager.create_env.assert_called_once_with(expected_path)

    def test_handle_name_too_long(self, tmp_path, mock_env_manager):
        handler = CafeCreateHandler(tmp_path, mock_env_manager)
        with pytest.raises(CafeEnvNameLengthError):
            handler.handle("a" * 26)

    def test_handle_invalid_symbols(self, tmp_path, mock_env_manager):
        handler = CafeCreateHandler(tmp_path, mock_env_manager)
        invalid_names = ["cafe name", "cafe!", "cafe.db", "@cafe"]
        for name in invalid_names:
            with pytest.raises(CafeEnvNameSymbolsError):
                handler.handle(name)

    def test_handle_already_exists(self, tmp_path, mock_env_manager):
        handler = CafeCreateHandler(tmp_path, mock_env_manager)
        (tmp_path / "existing.db").touch()
        with pytest.raises(CafeEnvExistsError):
            handler.handle("existing")


class TestCafeRemoveHandler:
    @pytest.fixture
    def mock_env_manager(self):
        return MagicMock()

    def test_handle_success(self, tmp_path, mock_env_manager):
        (tmp_path / "to_remove.db").touch()
        mock_env_manager.get_active_env_path.return_value = Path("other.db")
        handler = CafeRemoveHandler(tmp_path, mock_env_manager, tmp_path)
        
        handler.handle("to_remove")
        mock_env_manager.remove_env.assert_called_once_with(tmp_path / "to_remove.db")
        mock_env_manager.deactivate_env.assert_not_called()

    def test_handle_remove_active_deactivates(self, tmp_path, mock_env_manager):
        db_path = tmp_path / "active.db"
        db_path.touch()
        mock_env_manager.get_active_env_path.return_value = db_path
        handler = CafeRemoveHandler(tmp_path, mock_env_manager, tmp_path)
        
        handler.handle("active")
        mock_env_manager.deactivate_env.assert_called_once_with(tmp_path)

    def test_handle_not_found(self, tmp_path, mock_env_manager):
        mock_env_manager.remove_env.side_effect = FileNotFoundError
        handler = CafeRemoveHandler(tmp_path, mock_env_manager, tmp_path)
        with pytest.raises(CafeEnvNotFoundError):
            handler.handle("ghost")


class TestCafeActivateHandler:
    @pytest.fixture
    def mock_env_manager(self):
        return MagicMock()

    def test_handle_success(self, tmp_path, mock_env_manager):
        db_path = tmp_path / "target.db"
        db_path.touch()
        handler = CafeActivateHandler(tmp_path, mock_env_manager, tmp_path)
        
        handler.handle("target")
        mock_env_manager.activate_env.assert_called_once_with(db_path, tmp_path)

    def test_handle_not_found(self, tmp_path, mock_env_manager):
        handler = CafeActivateHandler(tmp_path, mock_env_manager, tmp_path)
        with pytest.raises(CafeEnvNotFoundError):
            handler.handle("missing")


class TestCafeDeactivateHandler:
    @pytest.fixture
    def mock_env_manager(self):
        return MagicMock()

    def test_handle_success(self, tmp_path, mock_env_manager):
        handler = CafeDeactivateHandler(tmp_path, mock_env_manager, tmp_path)
        handler.handle()
        mock_env_manager.deactivate_env.assert_called_once_with(tmp_path)

    def test_handle_no_active_env(self, tmp_path, mock_env_manager):
        mock_env_manager.deactivate_env.side_effect = FileNotFoundError
        handler = CafeDeactivateHandler(tmp_path, mock_env_manager, tmp_path)
        with pytest.raises(CafeEnvNoActiveError):
            handler.handle()


class TestCafeInitHandler:
    @pytest.fixture
    def mock_repos(self):
        return MagicMock(), MagicMock()

    def test_handle_success(self, mock_repos):
        cafe_repo, finance_repo = mock_repos
        cafe_repo.get.return_value = None
        finance_repo.get_primary.return_value = None
        
        handler = CafeInitHandler(cafe_repo, finance_repo)
        handler.handle("My Cafe", "Street 1", Money.from_any(500))
        
        cafe_repo.save.assert_called_once()
        finance_repo.save.assert_called_once()
        finance_repo.set_primary.assert_called_once()

    def test_handle_already_initialized(self, mock_repos):
        cafe_repo, finance_repo = mock_repos
        cafe_repo.get.return_value = MagicMock()
        
        handler = CafeInitHandler(cafe_repo, finance_repo)
        with pytest.raises(CafeEnvAlreadyInitError):
            handler.handle("Cafe", "Addr", Money.from_any(0))
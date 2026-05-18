import pytest
from pathlib import Path
from cafe_manager.infrastructure.env_manager import EnvironmentManager

class TestEnvironmentManager:
    @pytest.fixture
    def temp_storage(self, tmp_path):
        return tmp_path

    @pytest.fixture
    def manager(self, temp_storage, monkeypatch):
        monkeypatch.setattr("cafe_manager.infrastructure.env_manager.CAFES_STORAGE_DIR", temp_storage)
        monkeypatch.setattr("cafe_manager.infrastructure.env_manager.ACTIVE_ENV_FILENAME", ".active_test")
        return EnvironmentManager()

    def test_create_env_success(self, manager, temp_storage):
        name = "test_cafe"
        db_path = manager.create_env(name)
        
        assert db_path == temp_storage / "test_cafe.db"
        assert db_path.exists()
        assert db_path.is_file()

    def test_create_env_already_exists(self, manager, temp_storage):
        name = "duplicate"
        (temp_storage / "duplicate.db").touch()
        
        with pytest.raises(FileExistsError):
            manager.create_env(name)

    def test_remove_env_success(self, manager, temp_storage):
        name = "to_remove"
        db_path = temp_storage / "to_remove.db"
        db_path.touch()
        
        manager.remove_env(name)
        assert not db_path.exists()

    def test_remove_env_not_found(self, manager):
        with pytest.raises(FileNotFoundError):
            manager.remove_env("missing")

    def test_activate_env_success(self, manager, temp_storage):
        db_path = temp_storage / "active.db"
        manager.activate_env(db_path)
        
        active_file = temp_storage / ".active_test"
        assert active_file.exists()
        assert active_file.read_text(encoding="utf-8") == db_path.as_posix()

    def test_get_active_env_path_success(self, manager, temp_storage):
        db_path = temp_storage / "my_cafe.db"
        manager.activate_env(db_path)
        
        retrieved_path = manager.get_active_env_path()
        assert retrieved_path == db_path
        assert isinstance(retrieved_path, Path)

    def test_get_active_env_path_none(self, manager):
        assert manager.get_active_env_path() is None

    def test_deactivate_env_success(self, manager, temp_storage):
        db_path = temp_storage / "db.db"
        manager.activate_env(db_path)
        active_file = temp_storage / ".active_test"
        assert active_file.exists()
        
        manager.deactivate_env()
        assert not active_file.exists()

    def test_deactivate_env_not_found(self, manager):
        with pytest.raises(FileNotFoundError):
            manager.deactivate_env()

    def test_get_active_env_path_strips_whitespace(self, manager, temp_storage):
        active_file = temp_storage / ".active_test"
        active_file.write_text("  /path/to/db.db  \n", encoding="utf-8")
        
        retrieved = manager.get_active_env_path()
        assert retrieved == Path("/path/to/db.db")

    def test_remove_active_env_deactivates_it(self, manager, temp_storage):
        name = "current"
        db_path = manager.create_env(name)
        manager.activate_env(db_path)
        
        active_file = temp_storage / ".active_test"
        assert active_file.exists()
        
        manager.remove_env(name)
        assert not db_path.exists()
        assert not active_file.exists()
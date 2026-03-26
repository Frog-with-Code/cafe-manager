import pytest
from pathlib import Path
from cafe_manager.infrastructure.sqlite.env_manager import EnvironmentManager

class TestEnvironmentManager:
    @pytest.fixture
    def manager(self):
        return EnvironmentManager(active_env_filename=".test_active")

    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path

    def test_init_custom_filename(self):
        manager = EnvironmentManager(active_env_filename="custom.txt")
        assert manager.active_env_filename == "custom.txt"

    def test_create_env_success(self, manager, temp_dir):
        db_path = temp_dir / "subdir" / "test.db"
        manager.create_env(db_path)
        assert db_path.exists()
        assert db_path.is_file()

    def test_create_env_already_exists(self, manager, temp_dir):
        db_path = temp_dir / "exists.db"
        db_path.touch()
        with pytest.raises(FileExistsError):
            manager.create_env(db_path)

    def test_remove_env_success(self, manager, temp_dir):
        db_path = temp_dir / "remove.db"
        db_path.touch()
        manager.remove_env(db_path)
        assert not db_path.exists()

    def test_remove_env_not_found(self, manager, temp_dir):
        db_path = temp_dir / "missing.db"
        with pytest.raises(FileNotFoundError):
            manager.remove_env(db_path)

    def test_activate_env_success(self, manager, temp_dir):
        db_path = Path("/abs/path/to/cafe.db")
        manager.activate_env(db_path, temp_dir)
        
        active_file = temp_dir / ".test_active"
        assert active_file.exists()
        assert active_file.read_text() == db_path.as_posix()

    def test_activate_env_invalid_dir(self, manager, temp_dir):
        not_a_dir = temp_dir / "file.txt"
        not_a_dir.touch()
        with pytest.raises(NotADirectoryError):
            manager.activate_env(Path("db.db"), not_a_dir)

    def test_get_active_env_path_success(self, manager, temp_dir):
        db_path = Path("my_cafe.db")
        manager.activate_env(db_path, temp_dir)
        
        retrieved_path = manager.get_active_env_path(temp_dir)
        assert retrieved_path == db_path
        assert isinstance(retrieved_path, Path)

    def test_get_active_env_path_none(self, manager, temp_dir):
        assert manager.get_active_env_path(temp_dir) is None

    def test_deactivate_env_success(self, manager, temp_dir):
        manager.activate_env(Path("db.db"), temp_dir)
        active_file = temp_dir / ".test_active"
        assert active_file.exists()
        
        manager.deactivate_env(temp_dir)
        assert not active_file.exists()

    def test_deactivate_env_not_found(self, manager, temp_dir):
        with pytest.raises(FileNotFoundError):
            manager.deactivate_env(temp_dir)

    def test_get_active_env_path_strips_whitespace(self, manager, temp_dir):
        active_file = temp_dir / ".test_active"
        active_file.write_text("  /path/to/db.db  \n", encoding="utf-8")
        
        retrieved = manager.get_active_env_path(temp_dir)
        assert retrieved == Path("/path/to/db.db")
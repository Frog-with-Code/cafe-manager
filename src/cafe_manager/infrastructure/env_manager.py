from pathlib import Path
from cafe_manager.conf import CAFES_STORAGE_DIR, ACTIVE_ENV_FILENAME

class EnvironmentManager:
    def __init__(self):
        self._storage_dir = CAFES_STORAGE_DIR
        self._active_marker_path = CAFES_STORAGE_DIR / ACTIVE_ENV_FILENAME

    def activate_env(self, db_path: Path) -> None:
        if not self._storage_dir.is_dir():
            self._storage_dir.mkdir(parents=True, exist_ok=True)

        try:
            self._active_marker_path.write_text(db_path.as_posix(), encoding="utf-8")
        except OSError as e:
            raise OSError(f"Failed to write environment marker to {self._active_marker_path}") from e

    def get_active_env_path(self) -> Path | None:
        if not self._active_marker_path.exists():
            return None

        try:
            raw_path = self._active_marker_path.read_text(encoding="utf-8").strip()
            return Path(raw_path)
        except OSError:
            return None

    def create_env(self, name: str) -> Path:
        db_path = self._storage_dir / f"{name}.db"
        
        if db_path.exists():
            raise FileExistsError(f"Cafe environment '{name}' already exists")

        self._storage_dir.mkdir(parents=True, exist_ok=True)
        db_path.touch()
        return db_path

    def remove_env(self, name: str) -> None:
        db_path = self._storage_dir / f"{name}.db"
        
        if not db_path.exists():
            raise FileNotFoundError(f"Cafe environment '{name}' not found")

        active_path = self.get_active_env_path()
        if active_path and active_path.resolve() == db_path.resolve():
            self.deactivate_env()

        db_path.unlink()

    def deactivate_env(self) -> None:
        if not self._active_marker_path.exists():
            raise FileNotFoundError("No active environment to deactivate")
            
        self._active_marker_path.unlink()
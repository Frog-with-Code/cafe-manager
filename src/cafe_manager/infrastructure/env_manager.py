from pathlib import Path


class EnvironmentManager:
    def __init__(self, active_env_filename: str = ".active"):
        self.active_env_filename = active_env_filename

    def activate_env(self, db_path: Path, data_folder_path: Path) -> None:
        if not data_folder_path.is_dir():
            raise NotADirectoryError(
                f"Data folder path is not a directory: {data_folder_path}"
            )

        active_path = data_folder_path / self.active_env_filename

        try:
            active_path.write_text(db_path.as_posix(), encoding="utf-8")
        except OSError as e:
            raise OSError(f"Failed to write environment marker") from e

    def get_active_env_path(self, data_folder_path: Path) -> Path | None:
        active_path = data_folder_path / self.active_env_filename
        if not active_path.exists():
            return None

        raw_path = active_path.read_text(encoding="utf-8").strip()
        return Path(raw_path)

    def create_env(self, db_path: Path) -> None:
        if db_path.exists():
            raise FileExistsError(f"File with path '{db_path}' already exists")

        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.touch()

    def remove_env(self, db_path: Path) -> None:
        if not db_path.exists():
            raise FileNotFoundError(f"Impossible to remove unexistent file: {db_path}")

        db_path.unlink()

    def deactivate_env(self, data_folder_path: Path) -> None:
        active_path = data_folder_path / self.active_env_filename

        if not active_path.exists():
            raise FileNotFoundError(
                f"Impossible to remove unexistent file: {active_path}"
            )
        active_path.unlink()

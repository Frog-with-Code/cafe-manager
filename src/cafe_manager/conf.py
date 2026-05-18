import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

DEFAULT_STORAGE_DIR = PROJECT_ROOT / "cafes"
CAFES_STORAGE_DIR = Path(os.getenv("CAFE_STORAGE_DIR", DEFAULT_STORAGE_DIR))

ACTIVE_ENV_FILENAME = ".active"
ACTIVE_ENV_FILE_PATH = CAFES_STORAGE_DIR / ACTIVE_ENV_FILENAME

CAFES_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
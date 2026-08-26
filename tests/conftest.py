import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in [str(ROOT_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.core.config import settings
import app.db.repository as repo_module


@pytest.fixture(autouse=True)
def isolate_test_db(tmp_path: Path):
    """Ensure each test runs with an isolated clean SQLite database."""
    test_db = tmp_path / "test_risk_x.db"
    orig_path = settings.DATABASE_PATH
    settings.DATABASE_PATH = str(test_db)
    repo_module._repository_instance = None
    yield
    settings.DATABASE_PATH = orig_path
    repo_module._repository_instance = None

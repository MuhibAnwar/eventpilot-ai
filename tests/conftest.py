import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("GEMINI_API_KEY", "pytest-dummy-key")

import app.database as database
from app.database import init_db
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    init_db()
    with TestClient(app) as c:
        yield c
    if db_file.exists():
        os.unlink(db_file)

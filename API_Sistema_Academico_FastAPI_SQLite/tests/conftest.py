import pytest
from fastapi.testclient import TestClient

import app.database as database
from app.main import app


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "pruebas.db")
    with TestClient(app) as test_client:
        yield test_client


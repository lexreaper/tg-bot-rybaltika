import pytest
from fastapi.testclient import TestClient
from app.settings import get_app_settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.setenv('DEMO_DATABASE_URL', f'sqlite+aiosqlite:///{tmp_path}/test.db')
    get_app_settings.cache_clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    get_app_settings.cache_clear()



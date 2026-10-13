import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from app.settings import get_app_settings
from app.main import app
from app.db.session import get_session


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.setenv('DEMO_DATABASE_URL', f'sqlite+aiosqlite:///{tmp_path}/test.db')
    get_app_settings.cache_clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    get_app_settings.cache_clear()


def test_user_journey(client):
    assert client.get('/').status_code == 200
    categories = client.get('/menu/categories').json()
    assert len(categories) == 5
    assert [c['sort_order'] for c in categories] == sorted(c['sort_order'] for c in categories)
    category = categories[0]
    dishes = client.get(f"/menu?category_id={category['id']}").json()
    assert len(dishes) == category['dish_count'] == 3
    assert all(d['category_id'] == category['id'] for d in dishes)
    detail = client.get(f"/menu/dishes/{dishes[0]['id']}").json()
    assert detail == dishes[0]
    assert detail['description'] and detail['price'] == '890.00'
    assert client.get(detail['image_url']).headers['content-type'] == 'image/jpeg'


def test_unknown_category_and_dish(client):
    assert client.get('/menu/dishes/99999').status_code == 404
    assert client.get('/menu?category_id=99999').status_code == 404


@pytest.mark.parametrize('value', ['0', '-1', 'fish'])
def test_invalid_filter(client, value):
    assert client.get(f'/menu?category_id={value}').status_code == 422


def test_unavailable_dish_hidden(client):
    result = client.post('/menu/dishes', json={
        'category_id': 1, 'name': 'Hidden', 'description': None,
        'price': '100.00', 'image_url': None, 'is_available': False,
    })
    assert result.status_code == 201
    assert client.get(f"/menu/dishes/{result.json()['id']}").status_code == 404
    assert len(client.get('/menu?category_id=1').json()) == 3
    assert client.get('/menu/categories').json()[0]['dish_count'] == 3


def test_empty_category_and_fallback_fields(client):
    # Using the application's actual session and tables, rather than a fake API.
    from app.db.model import Category
    async def add_empty():
        async with app.state.session_factory() as session:
            session.add(Category(id=99, name='Скоро', sort_order=99))
            await session.commit()
    client.portal.call(add_empty)
    category = client.get('/menu/categories').json()[-1]
    assert category == {'id':99,'name':'Скоро','sort_order':99,'dish_count':0,'image_url':None}
    assert client.get('/menu?category_id=99').json() == []
    dish = client.get('/menu/dishes/3').json()
    assert dish['image_url'] is None


def test_database_failure_is_safe(client):
    async def broken_session():
        raise SQLAlchemyError('private connection details')
        yield
    app.dependency_overrides[get_session] = broken_session
    response = client.get('/menu/categories')
    assert response.status_code == 503
    assert 'private' not in response.text
    assert response.json()['detail']


def test_demo_seeding_is_idempotent(client):
    from app.demo import seed_demo
    async def seed_again():
        async with app.state.session_factory() as session:
            await seed_demo(session)
    client.portal.call(seed_again)
    assert len(client.get('/menu').json()) == 8


def test_config_and_assets(client):
    assert client.get('/app-config').json() == {'demo_mode': True}
    for asset in ['app.js','styles.css','config.js']:
        assert client.get('/assets/'+asset).status_code == 200

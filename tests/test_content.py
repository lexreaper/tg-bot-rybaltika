import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError

from app.db.content import Event, LoyaltyPage, Vacancy
from app.db.session import get_session
from app.main import app
from app.settings import get_app_settings

# A test-only value; the application has no built-in/default administrator key.
KEY = 'test-only-content-key-0123456789012345'


def authorize(monkeypatch):
    monkeypatch.setenv('CONTENT_ADMIN_TOKEN', KEY)
    get_app_settings.cache_clear()
    return {'X-Admin-Token': KEY}


def test_public_content_reads_published_sorted(client):
    response = client.get('/events')
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2
    assert [e['date'] for e in events] == sorted(e['date'] for e in events)
    assert set(events[0]) == {'id','title','description','date','image_url'}
    assert client.get(events[0]['image_url']).status_code == 200
    vacancies = client.get('/vacancies').json()
    assert len(vacancies) == 3
    assert vacancies[1]['salary'] is None
    assert 'Черновик' not in str(events+vacancies)
    page = client.get('/loyalty').json()
    assert page['body'] and page['title']
    assert 'version' not in page and 'is_published' not in page


def test_empty_lists_and_unpublished_page(client):
    from sqlalchemy import update
    async def hide():
        async with app.state.session_factory() as session:
            for model in [Event,Vacancy,LoyaltyPage]:
                await session.execute(update(model).values(is_published=False))
            await session.commit()
    client.portal.call(hide)
    assert client.get('/events').json() == []
    assert client.get('/vacancies').json() == []
    assert client.get('/loyalty').json() is None


def test_admin_disabled_until_configured(client, monkeypatch):
    monkeypatch.delenv('CONTENT_ADMIN_TOKEN', raising=False)
    get_app_settings.cache_clear()
    assert client.get('/admin/loyalty').status_code == 503


def test_loyalty_editor_permissions(client, monkeypatch):
    headers = authorize(monkeypatch)
    assert client.get('/admin/loyalty').status_code == 401
    assert client.get('/admin/loyalty',headers={'X-Admin-Token':'wrong'}).status_code == 401
    assert client.get('/admin/loyalty',headers=headers).status_code == 200
    assert client.put('/admin/loyalty',json={}).status_code == 401
    assert KEY not in client.get('/app-config').text


def test_editor_persists_and_publishes_content(client, monkeypatch):
    headers = authorize(monkeypatch)
    original = client.get('/admin/loyalty',headers=headers).json()
    payload = {'title':'Новое название','summary':'Короткий текст','body':'Первый абзац.\n\nВторой абзац.', 'is_published':True,'expected_version':original['version']}
    response = client.put('/admin/loyalty',headers=headers,json=payload)
    assert response.status_code == 200
    assert response.json()['version'] == original['version']+1
    assert client.get('/loyalty').json()['body'] == payload['body']
    # Re-running the demo bootstrap must not overwrite an administrator's text.
    from app.demo_content import seed_demo_content
    async def reseed():
        async with app.state.session_factory() as session:
            await seed_demo_content(session)
    client.portal.call(reseed)
    assert client.get('/loyalty').json()['title'] == 'Новое название'
    payload.update(is_published=False,expected_version=response.json()['version'])
    assert client.put('/admin/loyalty',headers=headers,json=payload).status_code == 200
    assert client.get('/loyalty').json() is None
    assert client.get('/admin/loyalty',headers=headers).json()['body'] == payload['body']


def test_editor_rejects_stale_version(client, monkeypatch):
    headers = authorize(monkeypatch)
    version = client.get('/admin/loyalty',headers=headers).json()['version']
    payload = {'title':'Версия 1','summary':'','body':'Сохранённый текст','is_published':True,'expected_version':version}
    assert client.put('/admin/loyalty',headers=headers,json=payload).status_code == 200
    payload['body']='Старый редактор пытается затереть изменения'
    assert client.put('/admin/loyalty',headers=headers,json=payload).status_code == 409
    assert client.get('/loyalty').json()['body']=='Сохранённый текст'


@pytest.mark.parametrize('field,value',[('title','  '),('body',''),('summary','x'*301),('body','x'*10001),('expected_version',-1)])
def test_editor_validates_content(client,monkeypatch,field,value):
    headers=authorize(monkeypatch)
    payload={'title':'Название','summary':'','body':'Текст','is_published':True,'expected_version':1}
    payload[field]=value
    assert client.put('/admin/loyalty',headers=headers,json=payload).status_code==422


def test_create_loyalty_in_empty_database(client,monkeypatch):
    headers=authorize(monkeypatch)
    from sqlalchemy import delete
    async def clear_page():
        async with app.state.session_factory() as session:
            await session.execute(delete(LoyaltyPage));await session.commit()
    client.portal.call(clear_page)
    assert client.get('/loyalty').json() is None
    assert client.get('/admin/loyalty',headers=headers).json()['version']==0
    payload={'title':'Первая страница','summary':'','body':'Первый текст','is_published':True,'expected_version':0}
    assert client.put('/admin/loyalty',headers=headers,json=payload).status_code==200
    assert client.get('/loyalty').json()['body']=='Первый текст'


@pytest.mark.parametrize('endpoint',['/events','/vacancies','/loyalty'])
def test_new_sections_handle_database_errors(client,endpoint):
    async def broken_session():
        raise SQLAlchemyError('private database credentials')
        yield
    app.dependency_overrides[get_session]=broken_session
    response=client.get(endpoint)
    assert response.status_code==503
    assert 'credentials' not in response.text


def test_existing_schema_migrates_without_losing_menu(tmp_path,monkeypatch):
    from app.db.config import get_database_settings
    for name in ['DB_HOST','DB_NAME','DB_USER','DB_PASSWORD']:
        monkeypatch.setenv(name,'test-placeholder')
    get_database_settings.cache_clear()
    engine=create_engine(f'sqlite:///{tmp_path}/migration.db')
    try:
        with engine.begin() as connection:
            config=Config('alembic.ini');config.attributes['connection']=connection
            command.upgrade(config,'70093c39af40')
            connection.exec_driver_sql("INSERT INTO categories (id,name,sort_order) VALUES (1,'Сохраняем меню',0)")
            command.upgrade(config,'head')
            assert connection.exec_driver_sql('SELECT name FROM categories WHERE id=1').scalar_one()=='Сохраняем меню'
            assert connection.exec_driver_sql('SELECT count(*) FROM events').scalar_one()==0
            assert connection.exec_driver_sql('SELECT count(*) FROM vacancies').scalar_one()==0
            assert connection.exec_driver_sql('SELECT count(*) FROM loyalty_page').scalar_one()==0
    finally:
        engine.dispose();get_database_settings.cache_clear()

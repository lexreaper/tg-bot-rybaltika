"""Demo app: python run_demo.py; with a local editor: python run_demo.py --editor."""
import argparse
import os
import secrets

import uvicorn

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Демонстрация Рыбалтики на http://127.0.0.1:8000')
    parser.add_argument('--editor', action='store_true', help='Включить редактор лояльности и показать ключ доступа в этой консоли')
    args = parser.parse_args()
    os.environ['DEMO_MODE'] = 'true'
    if args.editor:
        os.environ.setdefault('CONTENT_ADMIN_TOKEN', secrets.token_urlsafe(32))
        print('\nРедактор: http://127.0.0.1:8000/admin', flush=True)
        print('Ключ доступа для этого запуска: ' + os.environ['CONTENT_ADMIN_TOKEN'], flush=True)
        print('Вставьте ключ в редактор. Не публикуйте его в репозитории.\n', flush=True)
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000)

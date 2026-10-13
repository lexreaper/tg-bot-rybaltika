"""Run from the project folder: python run_demo.py."""
import os
import uvicorn

if __name__ == '__main__':
    os.environ['DEMO_MODE'] = 'true'
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000)

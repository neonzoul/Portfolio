from fastapi.testclient import TestClient
import app.main as m
from app.db.session import create_db_and_tables

# Ensure DB schema is up to date for local smoke test
create_db_and_tables()

with TestClient(m.app) as c:
    reg = c.post('/register', json={'email': 'alice@example.com', 'password': 'secret123'})
    print('register:', reg.status_code)

    login = c.post('/login', data={'username': 'alice@example.com', 'password': 'secret123'})
    print('login:', login.status_code)

    if login.status_code == 200:
        token = login.json()['access_token']
        r = c.post('/users/me/apikeys', headers={'Authorization': f'Bearer {token}'})
        print('create key:', r.status_code)

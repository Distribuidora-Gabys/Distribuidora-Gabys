# tests/conftest.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_login_correcto(client):
    resp = client.post("/login", data={"usuario": "admin", "password": "1234"})
    assert resp.status_code == 302
    assert "/menu" in resp.location

def test_login_incorrecto(client):
    resp = client.post("/login", data={"usuario": "admin", "password": "wrong"})
    assert b"Credenciales incorrectas" in resp.data

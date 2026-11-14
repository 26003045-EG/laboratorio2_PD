from types import SimpleNamespace
from contextlib import nullcontext
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app import main as module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(module, 'init_db', lambda: None)
    monkeypatch.setattr(module.cache, 'refresh', lambda *a, **k: None)
    monkeypatch.setattr(module.cache, 'model', SimpleNamespace(predict=lambda x: np.array([10.] * len(x)), residual_sigma_=1))
    monkeypatch.setattr(module.cache, 'version', '7')
    monkeypatch.setattr(module, 'catalogs', lambda: ({5: 'Guatemala'}, {'a': 'A'}, {'a': (2, 1)}, {}))
    monkeypatch.setattr(module, 'feature_table', lambda rows: rows)
    monkeypatch.setattr(module, 'save_predictions', lambda *a: None)
    # Sin lifespan: estas pruebas aíslan el contrato de los servicios externos.
    return TestClient(module.app)


def test_contrato_prediccion(client):
    result = client.post('/v1/prediccion', json={'tienda_id': 5, 'fecha': '2027-01-01', 'familias': [{'familia_id': 'a', 'en_promocion': 0}]})
    assert result.status_code == 200
    data = result.json()
    assert data['version_modelo'] == '7' and data['calidad']['estado'] == 'ok'
    assert data['predicciones'][0]['cantidad_sugerida'] >= 0
    assert isinstance(data['predicciones'][0]['cantidad_sugerida'], int)


def test_sin_modelo(client, monkeypatch):
    monkeypatch.setattr(module.cache, 'model', None)
    assert client.get('/modelo').status_code == 503
    assert client.get('/health').status_code == 503


def test_administracion_no_disponible(client, monkeypatch):
    def unavailable(*a, **k):
        raise ConnectionError('Sin Airflow')
    monkeypatch.setattr(module, 'airflow_request', unavailable)
    assert client.post('/admin/reentrenar').status_code == 503


def test_estado_desconocido(client, monkeypatch):
    monkeypatch.setattr(module, 'airflow_request', lambda *a, **k: SimpleNamespace(status_code=404))
    assert client.get('/admin/reentrenar/no-existe').status_code == 404


@pytest.mark.parametrize('scheduler,expected', [('healthy', 'ok'), ('unhealthy', 'degradado')])
def test_salud_revisa_scheduler(client, monkeypatch, scheduler, expected):
    monkeypatch.setattr(module.cache, 'available', True)
    connection = SimpleNamespace(execute=lambda *a: None)
    monkeypatch.setattr(module, 'engine', SimpleNamespace(connect=lambda: nullcontext(connection)))
    monkeypatch.setattr(module.requests, 'get', lambda *a, **k: SimpleNamespace(
        status_code=200, json=lambda: {'metadatabase': {'status': 'healthy'}, 'scheduler': {'status': scheduler}}))
    response = client.get('/health')
    assert response.status_code == 200 and response.json()['estado'] == expected

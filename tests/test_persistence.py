"""Prueba real contra una PostgreSQL de pruebas aislada (configurada en CI)."""
import os
from datetime import date
import pytest
from sqlalchemy import create_engine, text
from app import database
from app.contracts import ObservationRequest, SaleRequest, Quality


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Requiere PostgreSQL de pruebas')
def test_observaciones_idempotentes(monkeypatch):
    engine = create_engine(os.environ['TEST_DATABASE_URL'])
    monkeypatch.setattr(database, 'engine', engine)
    database.init_db()
    req = ObservationRequest(tienda_id=999999, fecha=date(2025, 1, 1), ventas=[SaleRequest(familia_id='prueba', ventas=10)])
    quality = Quality(estado='ok')
    try:
        assert database.save_observations(req, quality) == 1
        assert database.save_observations(req, quality) == 0
        req.ventas[0].ventas = 12
        assert database.save_observations(req, quality) == 1
        with engine.connect() as con:
            assert con.execute(text('SELECT ventas FROM observaciones WHERE tienda_id=999999')).scalar_one() == 12
    finally:
        with engine.begin() as con:
            con.execute(text('DELETE FROM observaciones WHERE tienda_id=999999'))
            con.execute(text('DELETE FROM informes_observaciones WHERE tienda_id=999999'))
        engine.dispose()

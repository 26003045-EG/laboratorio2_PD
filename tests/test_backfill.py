import json
import sqlite3
import numpy as np
import pandas as pd
import pytest
from scripts import backfill as module


class Model:
    residual_sigma_ = 1

    def predict(self, x):
        return np.full(len(x), 10)


def setup(monkeypatch, work_path):
    data = pd.DataFrame([{'fecha': d, 'tienda_id': 1, 'familia_id': 'a', 'ventas': 10, 'en_promocion': 0}
                         for d in pd.date_range('2025-01-01', periods=3)])
    data.to_csv(work_path / 'historico_ventas.csv', index=False)
    monkeypatch.setenv('DATA_DIR', str(work_path))
    monkeypatch.setattr(module, 'catalogs', lambda: ({}, {}, {'a': (2, 1)}, {}))
    monkeypatch.setattr(module, 'feature_table', lambda df: df)
    return work_path / 'resultados.sqlite'


def test_reanuda_sin_duplicar(monkeypatch, work_path):
    db = setup(monkeypatch, work_path)
    calls = []
    def evaluate(df, costs, start, end):
        calls.append(start)
        assert df.fecha.max() <= start
        return Model(), None, df[df.fecha == start], {'datos_sha256': 'prueba'}
    monkeypatch.setattr(module, 'evaluate', evaluate)
    first = module.backfill('2025-01-01', '2025-01-02', str(db))
    second = module.backfill('2025-01-01', '2025-01-02', str(db))
    assert first == second and len(calls) == 2
    with sqlite3.connect(db) as con:
        assert con.execute('SELECT count(*) FROM predicciones').fetchone()[0] == 2


def test_fallo_parcial_permite_reanudar(monkeypatch, work_path):
    db = setup(monkeypatch, work_path)
    def evaluate(df, costs, start, end):
        if start.day == 2:
            raise RuntimeError('Interrupción')
        return Model(), None, df[df.fecha == start], {'datos_sha256': 'prueba'}
    monkeypatch.setattr(module, 'evaluate', evaluate)
    with pytest.raises(RuntimeError):
        module.backfill('2025-01-01', '2025-01-02', str(db))
    with sqlite3.connect(db) as con:
        assert con.execute('SELECT count(*) FROM resultados').fetchone()[0] == 1


@pytest.mark.parametrize('start,end', [('2025-01-03', '2025-01-01'), ('2024-01-01', '2025-01-01')])
def test_rangos_invalidos(monkeypatch, work_path, start, end):
    db = setup(monkeypatch, work_path)
    with pytest.raises(ValueError):
        module.backfill(start, end, str(db))

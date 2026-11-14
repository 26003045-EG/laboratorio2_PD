"""Registro MLflow real y exclusión mutua PostgreSQL con datos sintéticos."""
import os
import pandas as pd
import pytest
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from training import train as module
from training import evaluation


@pytest.mark.skipif(not os.getenv('TEST_DATABASE_URL'), reason='Requiere PostgreSQL de pruebas')
def test_bootstrap_baseline_y_rechazo(monkeypatch, work_path):
    monkeypatch.setenv('DATABASE_URL', os.environ['TEST_DATABASE_URL'])
    monkeypatch.setenv('MLFLOW_TRACKING_URI', (work_path / 'mlflow').as_uri())
    monkeypatch.setenv('RUNS_DIR', str(work_path / 'runs'))
    monkeypatch.setattr(module, 'init_db', lambda: None)
    monkeypatch.setattr(module, 'catalogs', lambda: ({}, {}, {'a': (2, 1)}, {}))
    df = pd.DataFrame([{'fecha': d, 'tienda_id': store, 'familia_id': 'a', 'ventas': 10 + d.dayofweek, 'en_promocion': 0}
                       for d in pd.date_range('2025-01-01', periods=130) for store in range(20)])
    monkeypatch.setattr(module, 'load_data', lambda: df)
    monkeypatch.setattr(evaluation, 'feature_table', lambda df: df[['tienda_id', 'familia_id', 'en_promocion']])
    monkeypatch.setattr(module, 'feature_table', evaluation.feature_table)
    monkeypatch.setattr(module, 'should_promote', lambda *args: False)
    first = module.train('bootstrap')
    assert first['promovido'] and first['motivo'] == 'bootstrap_baseline'
    client = MlflowClient()
    model = mlflow.sklearn.load_model(f"models:/{module.MODEL_NAME}/{first['version']}")
    assert hasattr(model, 'medians_')
    second = module.train('candidato_rechazado')
    assert not second['promovido'] and second['version'] == first['version']
    assert str(module.champion(client).version) == first['version']
    assert not module.train('bootstrap')['promovido']

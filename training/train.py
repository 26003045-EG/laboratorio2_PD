"""Entrenamiento auditado y promoci?n serializada mediante PostgreSQL."""
import json
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from mlflow.exceptions import MlflowException
from sqlalchemy import create_engine, text
from app.data import feature_table, catalogs
from app.database import init_db
from app.model_cache import MODEL_NAME, ALIAS
from app.business import metrics, should_promote
from training.evaluation import evaluate


def load_data():
    path = Path(os.getenv('DATA_DIR', '/project/data/entrada'))
    df = pd.read_csv(path / 'historico_ventas.csv', parse_dates=['fecha'])
    # Last-observed values overwrite historical records for same day/store/family.
    engine = create_engine(os.environ['DATABASE_URL'])
    observed = pd.read_sql('SELECT fecha,tienda_id,familia_id,ventas FROM observaciones', engine)
    if not observed.empty:
        observed['fecha'] = pd.to_datetime(observed['fecha'])
        observed['en_promocion'] = 0  # Observations omit promotions, never infer actual ones.
        key = ['fecha', 'tienda_id', 'familia_id']
        df = pd.concat([df, observed], ignore_index=True).drop_duplicates(key, keep='last')
    return df.sort_values('fecha').reset_index(drop=True)



def champion(client):
    try:
        return client.get_model_version_by_alias(MODEL_NAME, ALIAS)
    except MlflowException as exc:
        if exc.error_code != 'RESOURCE_DOES_NOT_EXIST':
            raise
        return None


def register(client, model, name, result, kind):
    with mlflow.start_run(run_name=name) as run:
        mlflow.log_params({'tipo': kind, 'datos_sha256': result['datos_sha256'], 'semilla': 42,
                          'criterio': 'supera_baseline_y_mejora_vigente_0.5_pct'})
        mlflow.log_dict(result, 'evaluacion.json')
        for label in ('baseline', 'candidato', 'vigente'):
            for key, value in result.get(label, {}).items():
                mlflow.log_metric(f'{label}_{key}', value)
        for label, window in result['ventanas'].items():
            mlflow.log_params({f'{label}_{k}': v for k, v in window.items()})
        info = mlflow.sklearn.log_model(model, artifact_path='modelo', registered_model_name=MODEL_NAME)
        version = str(info.registered_model_version)
        if not version or version == 'None':
            own = [v for v in client.search_model_versions(f"name='{MODEL_NAME}'") if v.run_id == run.info.run_id]
            if not own:
                raise RuntimeError('No se encontr? la versi?n registrada')
            version = str(own[0].version)
        client.set_model_version_tag(MODEL_NAME, version, 'tipo', kind)
        client.set_model_version_tag(MODEL_NAME, version, 'decision', result['decision'])
        return version


def train(run_id='bootstrap'):
    os.environ.setdefault('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
    mlflow.set_tracking_uri(os.environ['MLFLOW_TRACKING_URI'])
    mlflow.set_experiment('NovaMercado | pronostico diario')
    client = MlflowClient()
    init_db()
    engine = create_engine(os.environ['DATABASE_URL'])
    # El bloqueo se conserva durante entrenamiento y promoci?n, incluso entre procesos.
    with engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
        connection.execute(text('SELECT pg_advisory_lock(26003045)'))
        try:
            old = champion(client)
            if run_id == 'bootstrap' and old is not None:
                return {'promovido': False, 'version': str(old.version), 'motivo': 'Modelo vigente persistido'}
            costs = catalogs()[2]
            df = load_data()
            model, baseline, val, result = evaluate(df, costs)
            old_cost = None
            if old is not None:
                incumbent = mlflow.sklearn.load_model(f'models:/{MODEL_NAME}/{old.version}')
                result['vigente'] = metrics(val.ventas.to_numpy(), incumbent.predict(feature_table(val)),
                                            val.familia_id, costs, incumbent.residual_sigma_)
                old_cost = result['vigente']['costo_medio']
            promote = should_promote(result['candidato']['costo_medio'], result['baseline']['costo_medio'], old_cost)
            result['decision'] = 'promover_candidato' if promote else ('bootstrap_baseline' if old is None else 'conservar_vigente')
            candidate_version = register(client, model, f'candidato_{run_id}', result, 'candidato')
            version = candidate_version if promote else (str(old.version) if old else None)
            if old is None and not promote:
                version = register(client, baseline, f'baseline_{run_id}', result, 'baseline')
            changed = promote or old is None
            if changed:
                client.set_registered_model_alias(MODEL_NAME, ALIAS, version)
            info = {'promovido': changed, 'version': version, 'version_candidato': candidate_version,
                    'motivo': result['decision'], **result}
            out = Path(os.getenv('RUNS_DIR', '/shared/runs'))
            out.mkdir(parents=True, exist_ok=True)
            target = out / (run_id.replace('/', '_').replace('\\', '_') + '.json')
            temp = target.with_suffix('.tmp')
            temp.write_text(json.dumps(info, ensure_ascii=False), encoding='utf-8')
            temp.replace(target)
            print(json.dumps(info, ensure_ascii=False))
            return info
        finally:
            connection.execute(text('SELECT pg_advisory_unlock(26003045)'))


if __name__ == '__main__':
    train(sys.argv[1] if len(sys.argv) > 1 else 'bootstrap')

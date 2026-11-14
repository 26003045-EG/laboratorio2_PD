"""Reprocesamiento histórico reanudable, sin alterar el alias champion."""
import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path
import pandas as pd
from app.business import suggestions
from app.data import catalogs, feature_table
from training.evaluation import evaluate

POLICY = 'temporal-cal28-hgb70-v1'


def backfill(start, end, database='shared/backfill/resultados.sqlite', tracking_uri=None):
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    if pd.isna(start) or pd.isna(end) or start > end:
        raise ValueError('Rango de fechas inválido')
    source = Path(os.environ.get('DATA_DIR', 'data/entrada')) / 'historico_ventas.csv'
    df = pd.read_csv(source, parse_dates=['fecha'])
    if start < df.fecha.min() or end > df.fecha.max():
        raise ValueError('El rango debe estar cubierto por el histórico')
    costs = catalogs()[2]
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    reports = []
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE IF NOT EXISTS resultados (clave TEXT PRIMARY KEY, fecha TEXT, informe TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS predicciones (clave TEXT, tienda INT, familia TEXT, esperado REAL, sugerido INT, PRIMARY KEY(clave, tienda, familia))')
        for day in pd.date_range(start, end):
            # Huella solo de información utilizada hasta este día; no depende de días futuros.
            available = df[df.fecha <= day].sort_values(['fecha', 'tienda_id', 'familia_id'])
            signature = hashlib.sha256((available.to_csv(index=False) + json.dumps(costs, sort_keys=True) + POLICY).encode()).hexdigest()
            key = f'{day.date()}-{signature}'
            previous = db.execute('SELECT informe FROM resultados WHERE clave=?', (key,)).fetchone()
            if previous:
                reports.append(json.loads(previous[0]))
                continue
            model, _, val, report = evaluate(available, costs, day, day)
            report.update({'fecha': str(day.date()), 'clave': key, 'politica': POLICY})
            predicted = model.predict(feature_table(val))
            suggested = suggestions(predicted, val.familia_id, costs, model.residual_sigma_)
            if tracking_uri:
                import mlflow
                mlflow.set_tracking_uri(tracking_uri)
                mlflow.set_experiment('NovaMercado | backfill')
                existing = mlflow.search_runs(filter_string=f"tags.backfill_key = '{key}'")
                if existing.empty:
                    with mlflow.start_run(run_name=f'backfill_{day.date()}', tags={'backfill_key': key}):
                        mlflow.log_dict(report, 'evaluacion.json')
                        mlflow.log_params({'datos_sha256': report['datos_sha256'], 'politica': POLICY})
                        mlflow.log_metrics({f'{label}_{k}': v for label in ('baseline', 'candidato') for k, v in report[label].items()})
                        mlflow.sklearn.log_model(model, artifact_path='modelo',
                                                pip_requirements=['scikit-learn==1.6.1', 'pandas==2.2.3', 'numpy==1.26.4'])
            with db:
                db.executemany('INSERT OR REPLACE INTO predicciones VALUES (?,?,?,?,?)',
                               [(key, int(row.tienda_id), str(row.familia_id), max(float(y), 0), int(q))
                                for row, y, q in zip(val.itertuples(), predicted, suggested)])
                db.execute('INSERT INTO resultados VALUES (?,?,?)', (key, str(day.date()), json.dumps(report)))
            reports.append(report)
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inicio', required=True)
    parser.add_argument('--fin', required=True)
    parser.add_argument('--database', default='shared/backfill/resultados.sqlite')
    parser.add_argument('--tracking-uri', default=os.getenv('MLFLOW_TRACKING_URI'))
    args = parser.parse_args()
    print(json.dumps(backfill(args.inicio, args.fin, args.database, args.tracking_uri), ensure_ascii=False, indent=2))

from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator


def reprocesar(**context):
    import os
    from scripts.backfill import backfill
    conf = context['dag_run'].conf
    backfill(conf['inicio'], conf['fin'], '/shared/backfill/resultados.sqlite', os.environ['MLFLOW_TRACKING_URI'])


with DAG('novamercado_backfill', start_date=datetime(2025, 1, 1),
         schedule=None, catchup=False, max_active_runs=1,
         tags=['novamercado', 'backfill']) as dag:
    PythonOperator(task_id='reprocesar_fechas', python_callable=reprocesar, retries=1)

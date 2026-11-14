from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator


def reentrenar(**context):
    from training.train import train
    return train(context['dag_run'].conf.get('run_id', context['dag_run'].run_id))


with DAG('novamercado_reentrenamiento', start_date=datetime(2025, 1, 1),
         schedule=None, catchup=False, max_active_runs=1, is_paused_upon_creation=False,
         dagrun_timeout=timedelta(minutes=10), tags=['novamercado', 'ml']) as dag:
    PythonOperator(task_id='entrenar_evaluar_y_promover', python_callable=reentrenar,
                   execution_timeout=timedelta(minutes=10), retries=0)

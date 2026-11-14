"""Comprobaciones con contenedores reales. Ejecutar en la raíz del proyecto."""
import json
import subprocess
import time
from pathlib import Path
import requests


def compose(*args):
    return subprocess.run(['docker', 'compose', *args], check=True, text=True, capture_output=True).stdout


def wait(check, limit):
    start = time.monotonic()
    while time.monotonic() - start < limit:
        try:
            if check():
                return round(time.monotonic() - start, 2)
        except requests.RequestException:
            pass
        time.sleep(2)
    raise TimeoutError(f'No se alcanzó el estado esperado en {limit} segundos')


def health(status):
    response = requests.get('http://localhost:8000/health', timeout=10)
    return response.status_code == 200 and response.json()['estado'] == status


def verify():
    result = {}
    mlflow_stopped = False
    try:
        compose('build')  # Excluido del tiempo máximo de inicio.
        started = time.monotonic()
        compose('up', '-d')
        result['inicio_segundos'] = round(time.monotonic() - started + wait(lambda: health('ok'), 600), 2)
        assert result['inicio_segundos'] <= 600
        observation = json.loads(Path('data/ejemplos/observacion_valida.json').read_text(encoding='utf-8'))
        for _ in range(2):
            response = requests.post('http://localhost:8000/v1/observaciones', json=observation, timeout=15)
            response.raise_for_status()
        assert response.json()['registros_guardados'] == 0
        result['observacion_idempotente'] = True
        response = requests.post('http://localhost:8000/admin/reentrenar', timeout=15)
        assert response.status_code == 202
        run_id = response.json()['id']
        state = {}
        def completed():
            nonlocal state
            response = requests.get(f'http://localhost:8000/admin/reentrenar/{run_id}', timeout=15)
            response.raise_for_status()
            state = response.json()
            return state['estado'] != 'en_curso'
        result['reentrenamiento_segundos'] = wait(completed, 600)
        assert state['estado'] == 'exitoso'
        result['decision'] = state
        result['actualizacion_segundos'] = wait(lambda: requests.get('http://localhost:8000/modelo', timeout=10).json()['version'] == state['version'], 120)
        compose('stop', 'mlflow')
        mlflow_stopped = True
        result['deteccion_caida_segundos'] = wait(lambda: health('degradado'), 60)
        prediction = json.loads(Path('data/ejemplos/prediccion_valida.json').read_text(encoding='utf-8'))
        assert requests.post('http://localhost:8000/v1/prediccion', json=prediction, timeout=30).status_code == 200
        result['predice_sin_mlflow'] = True
        compose('up', '-d', 'mlflow')
        mlflow_stopped = False
        result['recuperacion_segundos'] = wait(lambda: health('ok'), 120)
        version = requests.get('http://localhost:8000/modelo', timeout=10).json()['version']
        count_sql = 'SELECT count(*) FROM observaciones'
        before = compose('exec', '-T', 'db', 'psql', '-U', 'nova', '-d', 'nova', '-tAc', count_sql).strip()
        compose('down')
        compose('up', '-d')
        wait(lambda: health('ok'), 600)
        after = compose('exec', '-T', 'db', 'psql', '-U', 'nova', '-d', 'nova', '-tAc', count_sql).strip()
        assert before == after
        assert requests.get('http://localhost:8000/modelo', timeout=10).json()['version'] == version
        result['persistencia'] = True
        result['estado'] = 'correcto'
    except Exception as exc:
        result.update(estado='fallido', motivo=str(exc))
        raise
    finally:
        if mlflow_stopped:
            compose('up', '-d', 'mlflow')
        Path('evidencias/operacion.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    verify()

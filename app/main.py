import math
import os
import time
import uuid
import asyncio
from contextlib import asynccontextmanager
from datetime import date
import requests
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import text
from .cleaning import normalize_payload
from .contracts import PredictionResponse, PredictionItem, ObservationResponse
from .data import catalogs, feature_table
from .business import suggestions
from .database import engine, init_db, save_predictions, save_observations
from .model_cache import cache, MODEL_NAME, ALIAS

AIRFLOW_URL = os.getenv('AIRFLOW_URL', 'http://airflow-webserver:8080')
AIRFLOW_USER = os.getenv('AIRFLOW_USER', 'admin')
AIRFLOW_PASSWORD = os.getenv('AIRFLOW_PASSWORD', 'admin')
DAG_ID = 'novamercado_reentrenamiento'

@asynccontextmanager
async def lifespan(app):
    init_db()
    try:
        cache.refresh(force=True)
    except Exception:
        pass
    async def refrescar():
        while True:
            await asyncio.to_thread(cache.refresh, True)
            await asyncio.sleep(15)
    task = asyncio.create_task(refrescar())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

app = FastAPI(title='NovaMercado | Servicio de predicción', version='1.0.0', lifespan=lifespan)


def airflow_request(method, path, payload=None, timeout=5):
    return requests.request(method, f'{AIRFLOW_URL}/api/v1/{path}', auth=(AIRFLOW_USER, AIRFLOW_PASSWORD),
                            json=payload, timeout=timeout)

@app.post('/v1/prediccion', response_model=PredictionResponse)
async def predecir(request: Request):
    raw = await request.json()
    stores, names, costs, _ = catalogs()
    req, q = normalize_payload(raw, 'prediccion', stores, names)
    cache.refresh()
    if cache.model is None:
        raise HTTPException(503, detail='Modelo aún no disponible')
    records = [{'fecha': req.fecha.isoformat(), 'tienda_id': req.tienda_id,
                'familia_id': x.familia_id, 'en_promocion': x.en_promocion} for x in req.familias]
    preds = cache.model.predict(feature_table(records))
    result = []
    for x, y in zip(req.familias, preds):
        y = max(0.0, float(y))
        sigma = float(getattr(cache.model, 'residual_sigma_', 0))
        suggestion = int(suggestions([y], [x.familia_id], costs, sigma)[0])
        result.append(PredictionItem(familia_id=x.familia_id, venta_esperada=round(y, 2), cantidad_sugerida=suggestion))
    save_predictions(req, q, cache.version, result)
    return PredictionResponse(tienda_id=req.tienda_id, fecha=req.fecha, version_modelo=cache.version,
                              predicciones=result, calidad=q)

@app.post('/v1/observaciones', response_model=ObservationResponse)
async def observar(request: Request):
    stores, names, _, _ = catalogs()
    req, q = normalize_payload(await request.json(), 'observaciones', stores, names)
    return ObservationResponse(registros_guardados=save_observations(req, q), calidad=q)

@app.post('/admin/reentrenar', status_code=202)
def reentrenar():
    run_id = 'api_' + uuid.uuid4().hex[:20]
    try:
        res = airflow_request('POST', f'dags/{DAG_ID}/dagRuns', {'dag_run_id': run_id, 'conf': {'run_id': run_id}})
        if res.status_code not in (200, 201):
            raise RuntimeError(f'Airflow {res.status_code}: {res.text[:200]}')
    except Exception as e:
        raise HTTPException(503, detail=f'No se pudo iniciar reentrenamiento: {e}')
    return {'id': run_id}

@app.get('/admin/reentrenar/{run_id}')
def estado_reentrenamiento(run_id: str):
    try:
        res = airflow_request('GET', f'dags/{DAG_ID}/dagRuns/{run_id}')
        if res.status_code == 404:
            raise HTTPException(404, detail='Ejecución desconocida')
        res.raise_for_status()
        state = res.json().get('state', '')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(503, detail=f'Airflow no disponible: {e}')
    if state in ('running', 'queued', 'scheduled'):
        return {'estado': 'en_curso'}
    if state not in ('success', 'failed'):
        return {'estado': 'en_curso'}
    from pathlib import Path
    import json
    file = Path('/shared/runs') / (run_id + '.json')
    info = json.loads(file.read_text()) if file.exists() else {}
    cache.refresh(force=True)
    return {'estado': 'exitoso' if state == 'success' else 'fallido',
            'promovido': bool(info.get('promovido', False)), 'version': str(cache.version or ''),
            'motivo': info.get('motivo', 'Finalizado sin detalle adicional')}

@app.get('/modelo')
def modelo():
    cache.refresh()
    if cache.model is None:
        raise HTTPException(503, detail='Modelo aún no disponible')
    return {'nombre': MODEL_NAME, 'alias': ALIAS, 'version': cache.version}

@app.get('/health')
def health():
    reasons = []
    cache.refresh()
    if cache.model is None:
        raise HTTPException(503, detail='Modelo aún no disponible')
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
    except Exception:
        reasons.append('PostgreSQL no disponible')
    if not cache.available:
        reasons.append('MLflow no disponible; se usa modelo en memoria')
    try:
        resp = requests.get(f'{AIRFLOW_URL}/health', timeout=3)
        if resp.status_code != 200:
            reasons.append('Airflow no disponible')
    except Exception:
        reasons.append('Airflow no disponible')
    return {'estado': 'degradado' if reasons else 'ok', **({'motivo': '; '.join(reasons)} if reasons else {})}

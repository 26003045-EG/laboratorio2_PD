# laboratorio2_PD ? NovaMercado

Servicio de pron?stico diario para el Laboratorio 2 de Product Development. Basado en el c?digo entregado en `codigo completo/Laboratorio_2_ML`; se conserva su funcionalidad y se incorporan evaluaci?n temporal, backfill y desarrollo por ramas.

## Inicio

Requiere Python 3.11 para utilidades locales, Docker Desktop con contenedores Linux y Compose v2.

1. Colocar los cinco CSV oficiales en `data/entrada/`: `tiendas.csv`, `familias.csv`, `historico_ventas.csv`, `feriados.csv`, `costos.csv`.
2. Ejecutar `python scripts/preparar_env.py` para generar `.env` local.
3. Ejecutar `docker compose up --build -d`.
4. Consultar `http://localhost:8000/health` y `http://localhost:8000/docs`.

API: 8000. MLflow: 5000. Airflow: 8080, con las credenciales de `.env`. Las bases PostgreSQL del producto y de Airflow son independientes. No ejecutar ambos proyectos simult?neamente con los mismos puertos. El nombre Compose `laboratorio2-pd` separa los vol?menes de esta copia.

Los CSV y secretos no se publican ni se incluyen en las im?genes. Para detener y recuperar el estado: `docker compose down` y `docker compose up -d`, sin `-v`.

## Contrato

- `POST /v1/prediccion`: venta esperada, cantidad sugerida, calidad y versi?n por tienda/fecha.
- `POST /v1/observaciones`: registra ventas; repetir una observaci?n id?ntica devuelve cero cambios.
- `POST /admin/reentrenar`: sin cuerpo, responde 202 con un id o 503 si Airflow no est? disponible.
- `GET /admin/reentrenar/{id}`: estado y decisi?n de la ejecuci?n; 404 para id desconocido.
- `GET /modelo`: nombre, alias y versi?n del modelo cargado.
- `GET /health`: ok, degradado con motivo o 503 sin modelo.

Ejemplo en PowerShell:

```powershell
$body = Get-Content data/ejemplos/prediccion_valida.json -Raw
Invoke-RestMethod http://localhost:8000/v1/prediccion -Method Post -ContentType application/json -Body $body
```

## Modelo y negocio

Baseline: mediana hist?rica por familia. Candidato: HistGradientBoostingRegressor. Los ?ltimos 28 d?as son evaluaci?n, los 28 anteriores calibraci?n y los datos previos entrenamiento. La incertidumbre se estima en calibraci?n, nunca en evaluaci?n.

La m?trica principal usa los costos de faltantes y sobrantes de `costos.csv`. Tambi?n se reportan MAE, costo total, costo medio y mejora porcentual. La misma regla calcula cantidades sugeridas en API y evaluaci?n.

El candidato se promueve si supera al baseline y reduce al menos 0.5% el costo del campe?n sobre las mismas filas. En el primer arranque, si pierde, se registra el baseline como campe?n. Errores de MLflow no se interpretan como ausencia del modelo. Un bloqueo de PostgreSQL serializa entrenamientos y promociones.

La API comprueba el alias champion cada 15 segundos en segundo plano y conserva el modelo en memoria si MLflow falla.

## Backfill

Reprocesa fechas cubiertas por el hist?rico sin cambiar champion. Para cada d?a entrena y calibra con d?as anteriores; las ventas de ese d?a se usan despu?s para evaluar. Las promociones del d?a son conocidas al solicitar el pron?stico.

```powershell
python -m scripts.backfill --inicio 2026-02-27 --fin 2026-02-28
```

Los resultados y predicciones quedan en `shared/backfill/resultados.sqlite`, fuera de Git. Repetir el comando recupera resultados existentes; una interrupci?n permite continuar desde la ?ltima fecha completada. Una huella de datos, costos y pol?tica identifica la ejecuci?n. La fecha inicial necesita suficientes datos previos para entrenar y calibrar.

Para registrar modelos y m?tricas de backfill en MLflow:

```powershell
python -m scripts.backfill --inicio 2026-02-27 --fin 2026-02-28 --tracking-uri http://localhost:5000
```

Usar una base nueva mediante `--database shared/backfill/con_mlflow.sqlite` si ya se ejecut? ese rango sin MLflow. Desde Airflow ejecutar el DAG `novamercado_backfill` con configuraci?n JSON `{"inicio":"2026-02-27","fin":"2026-02-28"}`. Ese DAG registra sus resultados en el experimento de backfill y no promociona modelos.

## Pruebas y resultados

```powershell
python -m pip install -r requirements.txt
$env:OMP_NUM_THREADS = '1'
python -m pytest tests/ -q
python -m scripts.validacion_offline
```

La validaci?n actual obtuvo costo medio baseline 91.6243 y candidato 37.9428: mejora 58.5888%. Evidencia: `evidencias/validacion_actual.json`. Los resultados originales se conservan en `evidencias/validacion_modelo.json` como antecedente, con otra calibraci?n; no son resultados del c?digo nuevo.

Para comprobar la operaci?n completa con Docker: `python -m scripts.verificar_operacion`.

Ver `evidencias/PRUEBAS.md` para distinguir comprobaciones realizadas y pendientes. CI usa datos sint?ticos y ejecuta las pruebas en pushes y PRs de main y develop.

## Desarrollo y entrega

Ramas main, develop y feature por funcionalidad; commits breves en espa?ol. Ver `IMPLEMENTACION.md` para el estado de publicaci?n. El repositorio GitHub previsto es privado: `26003045-EG/laboratorio2_PD`. El propietario debe dar acceso al equipo docente desde la configuraci?n de colaboradores.

Entrega identificada por el tag `entrega-lab2`, integrada de develop a main mediante PR.

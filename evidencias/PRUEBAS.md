# Evidencia actual

## Ejecutado en esta copia

- Python 3.11.16, dependencias de requirements.txt.
- `python -m pytest tests -q`: 31 aprobadas, 2 omitidas (requieren PostgreSQL de pruebas para persistencia y entrenamiento integrado con MLflow). Dos advertencias de dependencias; sin fallos.
- Compilaci?n de app, training, scripts y dags correcta.
- Validaci?n oficial: MAE baseline 109.8491, candidato 47.7160; costo medio baseline 91.6243, candidato 37.9428; reducci?n 58.5888%. Ventanas y huella en validacion_actual.json.
- Backfill de 2026-02-27 y 2026-02-28: 2 resultados y 240 predicciones; repetirlo no duplic? registros. Evidencia en backfill.json.
- Pruebas de contrato HTTP con TestClient, cach? ante ca?da y recuperaci?n de MLflow, costos asim?tricos, l?mites de promoci?n, ausencia de informaci?n futura y reanudaci?n tras fallo parcial.

## Pendiente de servicios reales

Docker no est? instalado en esta terminal. Se intent? `docker compose up --build -d` y no se encontr? el ejecutable. No est?n acreditados el inicio en diez minutos, reentrenamiento en diez minutos, actualizaci?n en dos minutos, detecci?n de ca?da en un minuto, recuperaci?n en dos minutos ni persistencia de vol?menes.

`python -m scripts.verificar_operacion` automatiza esas comprobaciones con Docker y genera operacion.json. El script construye im?genes, inicia servicios, env?a observaciones y predicciones, dispara un reentrenamiento, detiene temporalmente MLflow y reinicia el proyecto sin borrar vol?menes. Ejecutarlo en la ra?z tras preparar .env y datos.

CI ejecut? 31 pruebas y todas aprobaron, incluyendo PostgreSQL real y el registro, carga, alias y conservaci?n del campe?n en MLflow local. Evidencia: https://github.com/26003045-EG/laboratorio2_PD/actions/runs/43562724825. La prueba integrada fuerza el rechazo del candidato para comprobar que el baseline inicial se conserva. Esta ejecuci?n no valida Airflow ni Compose.

Un intento de registro MLflow local no pudo completarse por permisos de directorios temporales de Windows en este entorno. Las pruebas unitarias del registro s? se ejecutan, pero no sustituyen la integraci?n MLflow/Airflow/Docker.

## Antecedentes

validacion_modelo.json se copi? de la fuente original y usa la calibraci?n anterior. Sus cifras no corresponden a esta versi?n. No se generaron capturas ni ejecuciones ficticias.

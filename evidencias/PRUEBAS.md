# Evidencia actual

- Python 3.11.16, dependencias de requirements.txt.
- `python -m pytest tests -q`: 31 aprobadas, 2 omitidas (requieren PostgreSQL de pruebas para persistencia y entrenamiento integrado con MLflow). Dos advertencias de dependencias; sin fallos.
- Compilaci?n de app, training, scripts y dags correcta.
- Validaci?n oficial: MAE baseline 109.8491, candidato 47.7160; costo medio baseline 91.6243, candidato 37.9428; reducci?n 58.5888%. Ventanas y huella en validacion_actual.json.
- Backfill de 2026-02-27 y 2026-02-28: 2 resultados y 240 predicciones; repetirlo no duplic? registros. Evidencia en backfill.json.
- Pruebas de contrato HTTP con TestClient, cach? ante ca?da y recuperaci?n de MLflow, costos asim?tricos, l?mites de promoci?n, ausencia de informaci?n futura y reanudaci?n tras fallo parcial.

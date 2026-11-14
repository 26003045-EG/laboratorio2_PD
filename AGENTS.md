# Contexto para herramientas de programación
Producto: servicio NovaMercado del Laboratorio 2.
Contrato oficial: POST /v1/prediccion, POST /v1/observaciones, POST /admin/reentrenar, GET /admin/reentrenar/{id}, GET /modelo, GET /health.
Mantener política de correcciones documentada en DECISIONES.md. No introducir fuga de información futura. Registrar versiones MLflow con alias champion y mantener modelo en memoria al caer MLflow.
Comprobaciones mínimas: pytest -q y docker compose up --build -d; validar API 8000, MLflow 5000 y Airflow 8080. No subir CSV, credenciales ni volúmenes a Git.

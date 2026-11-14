# Decisiones técnicas — NovaMercado

## Datos defectuosos
- `tienda_id` numérico en texto y formato T05: **reparar**, después validar contra catálogo.
- Familia con mayúsculas, acentos, espacios y nombre visible: **reparar** por equivalencia única.
- Cantidad entera en texto o decimal exacto: **reparar**; no redondear fracciones.
- Fechas AAAA-MM-DD, DD/MM/AAAA y fecha ISO con 00:00:00: **reparar** cuando no hay ambigüedad.
- Familias faltantes en pronóstico: **advertir**, completar con promoción 0, sin afirmar que esa promoción ocurrió.
- Familia duplicada: **rechazar 422** porque no es inequívoco sumar ni sobrescribir.
- Alias `tienda`: **reparar** únicamente si no existe `tienda_id`.
- Venta negativa: **rechazar 422**; no convertir devoluciones en ventas ficticias.
- Observación idéntica repetida: **idempotencia**; retorna 0 modificaciones.
- Cantidad con coma `1,234` o `812,0`: **reparar** según regla explícita (grupos de 3=separador miles; otros=decimal), enteros exactos.
- Familia, tienda o fecha irrecuperable: **rechazar 422**.

## Variables disponibles al pronosticar
Tienda, familia, día, mes, día del año, promociones de la solicitud y feriados del calendario; nunca ventas futuras. Las observaciones posteriores se usan solo al reentrenar.

## Cantidad sugerida
Costo asimétrico `cfaltante*max(real-sugerido,0)+csobrante*max(sugerido-real,0)`.
Cuantil por familia `cfaltante/(cfaltante+csobrante)`; aproximación Normal sobre residual validación y mínimo 10% de predicción; inventario existente desconocido.

## Modelo y reemplazo

Baseline por mediana de ventas por familia, con mediana global para familias sin historia. Candidato HistGradientBoostingRegressor, semilla 42. Se eligi? por admitir relaciones no lineales sin una infraestructura adicional.

Separaci?n cronol?gica: entrenamiento anterior a los 56 d?as finales, calibraci?n de 28 d?as y evaluaci?n final de 28 d?as. As? el costo no usa una incertidumbre estimada con las respuestas de evaluaci?n. No se reentrena con esa ventana despu?s de medir para no registrar un modelo distinto del evaluado.

La promoci?n exige superar al baseline y mejorar al campe?n al menos 0.5% en costo medio, evaluados sobre las mismas observaciones. Este margen evita reemplazos por mejoras m?nimas. Con costo vigente cero no hay promoci?n por empate. M?tricas no finitas no autorizan reemplazo. Sin campe?n, un candidato que pierde deja al baseline registrado como campe?n: se prioriza disponibilidad sin declarar una mejora inexistente.

Se registran m?tricas, huella de datos, ventanas, versiones y motivo en MLflow. Fallos de acceso al registro abortan el entrenamiento en lugar de suponer que no existe campe?n. Un bloqueo asesor de PostgreSQL impide carreras entre bootstrap y reentrenamientos.

## Backfill

DAG separado, manual por rango de fechas. Reproduce entrenamiento, calibraci?n y evaluaci?n diaria usando solamente d?as anteriores para ajustar el modelo. Las ventas del d?a pronosticado solo sirven para medir despu?s. Las correcciones hist?ricas se procesan con una nueva huella; no se afirma que se conocieran en la fecha original. Es una simulaci?n retrospectiva con la versi?n de datos disponible, no una reconstrucci?n de auditor?a de cambios que la fuente no contiene.

Se usa SQLite local para reanudar por fecha y huella sin duplicar resultados. El DAG limita las ejecuciones simult?neas a una. No modifica champion ni las observaciones operativas. MLflow registra el linaje de los modelos retrospectivos sin promoverlos. Se eligi? un DAG separado para evitar que una revisi?n hist?rica sustituya el modelo operativo.

## Arquitectura
FastAPI se apoya en PostgreSQL propia y retiene el modelo cacheado para continuar prediciendo si MLflow cae. Sondeo del alias `champion` cada 15 segundos en segundo plano y al recibir peticiones. Tiempos de espera acotados al consultar MLflow. Airflow se ejecuta aparte con otra BD y dispara tareas con API REST básica. Compose mantiene volúmenes persistentes.

## Límites
La inferencia no utiliza lags de observaciones en tiempo real. El entrenamiento utiliza promociones reales del histórico; observaciones incrementales carecen de promociones y se rellenan a cero (supuesto documentado). Datos originales no versionados públicamente; docente debe colocar CSV en `data/entrada`.

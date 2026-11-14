# Estado del proyecto

Origen: `codigo completo/Laboratorio_2_ML`. Destino: esta carpeta independiente. Los originales se conservaron.

## Historial

main contiene la estructura inicial. develop integra progresivamente las ramas:

| Rama | Commit principal |
|---|---|
| feature/infraestructura | Prepara el proyecto |
| feature/contratos-limpieza | Valida los datos |
| feature/persistencia | Guarda las operaciones |
| feature/prediccion | Agrega predicciones |
| feature/evaluacion-negocio | Eval?a los modelos |
| feature/reentrenamiento | Actualiza el modelo |
| feature/backfill | Reprocesa fechas anteriores |
| feature/validacion-entrega | Prepara la entrega |

El c?digo inicial proviene de una implementaci?n ya existente; esta reorganizaci?n no simula una historia anterior. Los commits tienen fechas reales y mensajes breves en espa?ol.

## Publicaci?n

Repositorio privado: https://github.com/26003045-EG/laboratorio2_PD

Los PRs se crearon e integraron en orden sobre develop remoto, conservando las ramas y los commits originales. No se simularon revisiones ni aprobaciones. Los primeros siete est?n integrados; el octavo completa la validaci?n.

- `infraestructura`: https://github.com/26003045-EG/laboratorio2_PD/pull/1
- `contratos-limpieza`: https://github.com/26003045-EG/laboratorio2_PD/pull/2
- `persistencia`: https://github.com/26003045-EG/laboratorio2_PD/pull/3
- `prediccion`: https://github.com/26003045-EG/laboratorio2_PD/pull/4
- `evaluacion-negocio`: https://github.com/26003045-EG/laboratorio2_PD/pull/5
- `reentrenamiento`: https://github.com/26003045-EG/laboratorio2_PD/pull/6
- `backfill`: https://github.com/26003045-EG/laboratorio2_PD/pull/7
- `validacion-entrega`: https://github.com/26003045-EG/laboratorio2_PD/pull/8

Entrega a main en borrador: https://github.com/26003045-EG/laboratorio2_PD/pull/9

Docker no est? disponible en este equipo. El borrador y el tag entrega-lab2 quedan pendientes de verificar operaci?n, tiempos y persistencia. Consultar evidencias/PRUEBAS.md y ejecutar python -m scripts.verificar_operacion en un equipo con Docker. El propietario debe dar acceso al docente al repositorio privado.

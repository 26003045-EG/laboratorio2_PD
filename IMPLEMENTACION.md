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

## Publicaci?n pendiente

Nombre aprobado: `26003045-EG/laboratorio2_PD`, privado. Falta autenticaci?n de GitHub para crear el repositorio y los PRs. No se afirma que los merges locales sean PRs.

Al publicar, iniciar develop remoto desde el commit inicial y abrir los PRs de las ramas en el orden anterior, integr?ndolos con merge para conservar evidencia real. Posteriormente sincronizar develop local con el resultado remoto. El PR de develop a main y el tag entrega-lab2 quedan pendientes de las verificaciones de operaci?n.

Docker no est? disponible en este equipo. La matriz de verificaciones est? en evidencias/PRUEBAS.md. No se cre? el tag de entrega sin validar operaci?n.

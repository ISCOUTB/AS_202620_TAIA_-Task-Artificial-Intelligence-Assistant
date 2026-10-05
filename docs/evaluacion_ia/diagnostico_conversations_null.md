# Regresión del 500 al guardar una conversación

Fecha: 2026-10-05 UTC (2026-10-04 en Colombia).

## Evidencia y causa

La llamada piloto a `POST /ai/message` devolvió 500. El operador aportó el
traceback de Dokploy de las 03:18:38 UTC: `CheckViolation` de
`ck_conversations_pending_action_consistent`. El INSERT enviaba
`pending_action: Jsonb(None)` y `pending_action_expires_at: None`.
Se omiten identificadores de usuarios y cualquier dato de autenticación.

El mapeo `JSONB` convertía `None` a JSON null, que no es SQL NULL. La restricción
exige que la acción y su vencimiento estén ambos presentes o ambos ausentes.
La corrección es `JSONB(none_as_null=True)` en
[ConversationModel](../../backend/app/modules/ai/adapters/outbound/sqlalchemy_models.py).
La semántica está documentada en
[SQLAlchemy, parámetro none_as_null](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html#sqlalchemy.dialects.postgresql.JSON.__init__).
No se quita el CHECK, no se cambian tablas ni se requiere una migración por este
cambio de serialización. No se añade ninguna dependencia.

## Prueba roja y verde

[Prueba](../../backend/tests/test_conversation_null_binding.py): usa el procesador
real del dialecto psycopg sin abrir conexiones. Comprueba que la ausencia sea
SQL NULL y que una acción siga siendo un objeto Jsonb con el contenido intacto.

Antes de corregir: **1 failed, 1 passed**, con `assert Jsonb(None) is None`.
Después: **2 passed**. Para reproducir el defecto mediante mutación en memoria:

```powershell
.\.venv\Scripts\python.exe tools/demo_conversation_null_red.py
# Esperado: 1 failed, 1 passed; salida 1.
.\.venv\Scripts\python.exe -m pytest backend/tests/test_conversation_null_binding.py -q -p no:cacheprovider
# Esperado: 2 passed; salida 0.
```

Ejecutar sin `TEST_DATABASE_URL`. No se ejecutó una integración PostgreSQL local.
La mutación no modifica archivos ni necesita restaurar el árbol de trabajo.

## Despliegue y límite de la evidencia

La corrección está en el árbol local, sin commit. El servidor remoto no queda
corregido por editar este archivo. Es necesario construir y desplegar una imagen
que incluya el cambio; volver a desplegar el mismo commit remoto no lo incluye.
No hay acceso administrativo a Dokploy disponible en esta sesión.

Después del despliegue se debe repetir propuesta → confirmación → consulta de
la tarea persistida con una cuenta sintética. Este error puede ocultar un fallo
del proveedor: eliminarlo no demuestra por sí solo que Gemini esté funcionando.
S1 y S3 completos siguen sin resultado verificable; no se infiere calidad,
costo ni latencia del modelo de una respuesta 500.

# ADR-0005 — Normalización de la confirmación escrita en español

## Estado

Aceptado.

## Contexto

TAIA registra tareas desde Telegram o desde la app mediante lenguaje natural (aspectos [A-01](../aspectos.md) y [A-03](../aspectos.md)). El caso de uso `HandleUserMessageUseCase` interpreta el mensaje con el modelo de lenguaje, propone la escritura y **espera confirmación** antes de llamar a `academico`: el modelo piensa, `academico` valida y persiste.

Esa confirmación llega como texto libre del estudiante, no como un botón. Antes de esta decisión, `_resolve_pending` comparaba la respuesta contra dos conjuntos cerrados:

```python
answer = text.lower().strip(" .!?")
if answer in _YES:   # {"si", "s", "dale", "ok", "confirmo", "yes", "listo", "hazlo"}
```

El defecto D-S8-01 es que `_YES` solo contenía `si` **sin tilde**. Un estudiante que escribe `Sí`, que es la forma natural en español, produce `sí` tras `.lower()` y nunca coincide con el conjunto. La tarea no se creaba y el asistente respondía pidiendo confirmar una acción que el estudiante ya había confirmado. La prueba `backend/tests/test_ai_create_task_confirmation.py` reproduce el fallo: de 16 casos, fallaban exactamente los 7 acentuados.

El proyecto atiende una comunidad hispanohablante, y Telegram es el canal de captura rápida, así que el texto llega sin acentos y con signos con frecuencia.

## Escenario de calidad relacionado

**S1 — Exactitud de la interpretación** y **S3 — Latencia percibida** en [escenarios_calidad.md](../calidad/escenarios_calidad.md): la interpretación se considera correcta solo si la tarea llega a crearse cuando el estudiante la confirmó. Un falso negativo de confirmación es un fallo de exactitud, y además induce un segundo turno de conversación, lo que encarece la operación.

## Opciones consideradas

### Opción A — Normalizar acentos, mayúsculas y signos antes de comparar

Una función `_normalizar_respuesta` aplica `unicodedata.normalize("NFKD", ...)`, descarta los caracteres diacríticos con `unicodedata.combining`, pasa a minúsculas con `casefold()` y quita la puntuación de los extremos. `sí`, `Sí`, `SÍ`, `sí.`, `  sí  ` y `¡Sí!` colapsan en el mismo token `si`. Los conjuntos `_YES` y `_NO` no cambian.

### Opción B — Agregar cada variante acentuada a los conjuntos `_YES` y `_NO`

Enumerar `sí`, `sí.`, `¡sí!`, `Sí`, `SÍ` y sus combinaciones es combinatorial: cada signo y cada variante de capitalización multiplica el conjunto. El conjunto se vuelve un enumerado de variantes ortográficas en lugar de un conjunto de intenciones, y cada variante nueva exige modificar el código y sus pruebas.

### Opción C — Pedir al modelo de lenguaje que clasifique la respuesta

Encargar a Gemini la decisión de si el mensaje es una confirmación resuelve los acentos por saturación, pero convierte una operación determinista y verificable en una llamada de red: S3 empeora, el costo por operación sube y el resultado deja de ser reproducible en las pruebas. Además, la confirmación es la última barrera antes de escribir en la base: no debe depender de un componente no determinista.

## Decisión

Se adopta la **Opción A**.

La normalización es responsabilidad del caso de uso y ocurre una sola vez, en `_resolve_pending`, antes de comparar. Se usa `casefold()` en lugar de `lower()` porque `lower()` no reduce por completo ciertos caracteres no latinos. Las respuestas de más de una palabra, como `no, después`, siguen sin coincidir con ningún conjunto y quedan sin confirmar, que es el comportamiento seguro por defecto ante la duda.

## Consecuencias

### Positivas

- Las 16 formas de confirmación del conjunto de pruebas se resuelven con una función, y las variantes que se añadan en el futuro también.
- La prueba es determinista: no depende de red ni de `GEMINI_API_KEY`, así que corre en CI.
- La decisión queda justificada y registrada, en lugar de aparecer como un `.lower()` más en el código.
- `unicodedata` pertenece a la biblioteca estándar, así que no añade dependencia.

### Negativas

- Eliminar tildes es correcto para comparar intenciones, pero el texto original del estudiante **no se modifica**: se conserva en `conversation.record("user", text)`, con su acentuación intacta.
- La normalización solo se aplica a la confirmación. `MAX_INPUT_CHARS` se sigue contando sobre el texto original, sin cambios.
- El asistente solo reconoce las intenciones de los conjuntos cerrados. Un mensaje en otro idioma, o una confirmación expresada con palabras que no estén en `_YES`, se responde con `not_confirmed()` y no escribe nada.
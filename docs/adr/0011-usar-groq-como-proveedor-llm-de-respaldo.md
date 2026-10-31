# ADR-0011 — Usar Groq como proveedor LLM de respaldo

## Estado

Aceptado por el equipo el 2026-10-30; redactado con apoyo de IA a pedido del equipo. **Reemplaza
parcialmente a [ADR-0007](0007-comportamiento-ante-fallo-del-proveedor-llm.md)** en su punto 4
("sin reintentos automáticos ni respaldo"). El resto de ADR-0007 sigue vigente.

Implementación pendiente; dueño: dei0811 (amenaza T-15 de [modelo_amenazas.md](../modelo_amenazas.md)).

## Contexto

El módulo AI interpreta los mensajes con Gemini detrás de `LLMPort`
([ADR-0001](0001-estilo-arquitectonico.md)). Cuando Gemini falla, ADR-0007 hace que TAIA falle
cerrado: responde "Ahora no puedo procesar tu mensaje" y no escribe nada.

En octubre de 2026 el equipo observó que Gemini no responde con frecuencia por exceso de tráfico.
No hay una medición registrada de esa frecuencia. Con fallar cerrado, cada caída deja al asistente
inutilizable mientras dura. En el modelo de amenazas es T-15 (OWASP A10), con prioridad alta.

ADR-0007 descartó un respaldo (su opción C) por tres costos: un segundo adaptador, una segunda
credencial y una evaluación de exactitud propia, porque "un modelo distinto interpreta distinto".
El equipo ya tiene una credencial de Groq (`GROQ_API_KEY_1` en [.env.example](../../.env.example))
y considera que las caídas justifican esos costos.

## Escenarios de calidad relacionados

- **RF-AGT-20 / RNF-09:** una caída del LLM no impide usar el resto del sistema.
- **S1:** exactitud de la interpretación; un segundo modelo no puede bajarla sin que se note.
- **S3:** respuesta del asistente con p95 ≤ 7 s, que ahora puede incluir dos llamadas.

## Opciones consideradas

| Opción | Ventaja | Costo |
|---|---|---|
| A. Mantener ADR-0007 (solo fallar cerrado) | Sin código ni evaluación nuevos | El asistente no funciona mientras Gemini esté caído |
| B. Reemplazar Gemini por Groq | Un solo proveedor que mantener | Se pierden las mediciones de S1, S3 y S5 hechas con Gemini, y Groq también puede caerse |
| C. Groq como respaldo de Gemini | Una caída de un proveedor no detiene al asistente | Segundo adaptador, segunda evaluación y un segundo tercero que recibe mensajes |

## Decisión

Se adopta la **opción C**.

1. **Adaptador `GroqLLM`.** Implementa `LLMPort` y, igual que `GeminiLLM`, traduce todo fallo a
   `LLMError` (capa anticorrupción de ADR-0007). Modelo: `GROQ_MODEL` (`openai/gpt-oss-120b`).
2. **Composición.** Un `LLMPort` de respaldo llama a Gemini y, solo ante `LLMError`, llama a
   Groq. Si ambos fallan, propaga `LLMError` y el caso de uso responde como en ADR-0007. El caso
   de uso no cambia.
3. **Mismas garantías.** Groq recibe el mismo esquema JSON, las reglas en el mensaje de sistema y
   el texto delimitado de RF-AGT-18. Su salida pasa por la misma validación.
4. **Requisito para activarlo.** Groq se activa en producción solo después de evaluarlo con
   `tools/eval_llm.py` sobre el mismo conjunto de S1, con resultado registrado en
   `docs/evaluacion_ia/`.
5. **Credenciales.** Por variables de entorno (RNF-02). Sin la credencial de Groq, el sistema
   funciona como hoy: Gemini solo y falla cerrada.

## Consecuencias

### Positivas

- Una caída de Gemini deja de detener al asistente.
- El puerto `LLMPort` absorbe el cambio: dominio y casos de uso no se tocan (S5 de ADR-0007).

### Negativas

- Hay dos adaptadores y dos evaluaciones que mantener.
- Los mensajes del estudiante pueden llegar a un segundo tercero fuera de Colombia, lo que se
  declara en la autorización de RF-USR-10 ([modelo_amenazas.md §6](../modelo_amenazas.md#6-privacidad)).
- Una caída de Gemini por timeout suma hasta 20 s antes de intentar con Groq, y eso puede romper
  S3 en esos casos.

### Puntos abiertos

- Validar que `openai/gpt-oss-120b` en Groq acepta salida JSON con esquema.
- El uso de la segunda credencial (`GROQ_API_KEY_2`) queda fuera de esta decisión hasta revisar los
  términos de uso de Groq.

## Trazabilidad

| Eslabón | Referencia |
|---|---|
| Requisitos | RF-AGT-20, RNF-09, RNF-02 |
| Amenaza | T-15 en [modelo_amenazas.md](../modelo_amenazas.md) |
| Elementos C4 | Componente AI y sistema externo Proveedor LLM ([C4-C3](../c4/C4-C3.md)) |
| ADR relacionados | [ADR-0001](0001-estilo-arquitectonico.md), [ADR-0007](0007-comportamiento-ante-fallo-del-proveedor-llm.md) |
| Código y pruebas | Pendientes |

# ADR-0013 — Usar Groq como proveedor LLM principal y Gemini como respaldo

## Estado

Aceptado por el equipo el 2026-11-20. Redactado con apoyo de IA a pedido del equipo.
**Reemplaza a [ADR-0011](0011-usar-groq-como-proveedor-llm-de-respaldo.md)** en el orden de los
proveedores. El resto de ADR-0011 (mismas garantías, mismo contrato de interpretación, credenciales
por entorno) sigue vigente, y también ADR-0007: si fallan los dos proveedores, se falla cerrado.

Implementación: frente D del cierre S16.

## Contexto

ADR-0011 dejó a Gemini como proveedor principal y a Groq como respaldo. Desde entonces el equipo
observa que Gemini no responde con frecuencia, y en noviembre eso sigue pasando. Cada caída de
Gemini cuesta además la espera de su timeout antes de pasar a Groq. ADR-0011 ya registra que esa
espera puede romper S3.

Las dos evaluaciones sobre el mismo conjunto de 99 casos de S1, con el día de la semana incluido,
dan:

| Medida | Gemini | Groq | Fuente |
|---|---:|---:|---|
| Exactitud de intención (S1) | 92,93 % | 91,92 % | `S1_exactitud_intencion` |
| Latencia p50 (S3) | 1254,0 ms | 852,6 ms | `S3_latencia_ms` |
| Latencia p95 (S3) | 1690,3 ms | 1198,7 ms | `S3_latencia_ms` |
| Errores de llamada | 0 | 0 | `S3_latencia_ms.errores` |

Fuentes: [resultado_gemini_s1_100_con_dia.json](../evaluacion_ia/resultado_gemini_s1_100_con_dia.json)
y [resultado_groq_s1_100_con_dia.json](../evaluacion_ia/resultado_groq_s1_100_con_dia.json).

La diferencia de exactitud es de un caso de 99. Groq es un 29 % más rápido en el p95.

## Escenarios de calidad relacionados

- **S1:** exactitud de la interpretación.
- **S3:** respuesta del asistente con p95 ≤ 7 s.
- **RNF-09 y RF-AGT-20:** una caída del LLM no impide usar el resto del sistema.

## Opciones consideradas

| Opción | Ventaja | Costo |
|---|---|---|
| A. Mantener ADR-0011 (Gemini primero) | Un caso más de exactitud en S1 | Cada caída de Gemini suma su timeout a la respuesta |
| B. Groq primero y Gemini como respaldo | Menor latencia en el caso normal; las caídas de Gemini dejan de notarse | Un caso menos de exactitud en S1 |
| C. Solo Groq | Un único proveedor que mantener | Sin respaldo: una caída de Groq detiene al asistente (se vuelve a ADR-0007 puro) |

## Decisión

Se adopta la **opción B**.

1. **Orden.** `FallbackLLM` intenta primero Groq, con cada clave configurada, y solo ante
   `LLMError` intenta Gemini. Si fallan todos, propaga `LLMError` y el caso de uso falla cerrado
   (ADR-0007).
2. **Sin cambios en el contrato.** Los dos proveedores siguen compartiendo
   `interpretation_contract.py` y la misma validación de la salida.
3. **Evaluación.** Un cambio en las reglas de interpretación se evalúa primero con Groq
   (`tools/eval_llm.py --proveedor groq`). La evaluación con Gemini se hace cuando esté disponible
   y su resultado se registra en `docs/evaluacion_ia/`.

## Consecuencias

### Positivas

- En el caso normal responde el proveedor más rápido.
- Una caída de Gemini ya no afecta la latencia.

### Negativas

- Se pierde un caso de 99 de exactitud en S1 frente a Gemini.
- Las mediciones de S1, S3 y S5 de referencia pasan a ser las de Groq.

### Puntos abiertos

- La API todavía exige `GEMINI_API_KEY` para arrancar. Volverla opcional y exigir la de Groq cambia
  la configuración del despliegue y del CI, y queda fuera de esta decisión.
- El uso de `GROQ_API_KEY_2` sigue sujeto a los términos de uso de Groq (ADR-0011).

## Trazabilidad

| Eslabón | Referencia |
|---|---|
| Requisitos | RF-AGT-20, RNF-09, RNF-08 |
| Evidencia | `docs/evaluacion_ia/resultado_*_s1_100_con_dia.json` |
| Elementos C4 | Componente AI y sistema externo Proveedor LLM ([C4-C3](../c4/C4-C3.md)) |
| ADR relacionados | [ADR-0007](0007-comportamiento-ante-fallo-del-proveedor-llm.md), [ADR-0011](0011-usar-groq-como-proveedor-llm-de-respaldo.md) |
| Código y pruebas | Pendientes (frente D) |

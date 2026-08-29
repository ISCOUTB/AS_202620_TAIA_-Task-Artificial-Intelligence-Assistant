# Aspectos del sistema

| ID | Aspecto | Requisito | C4 | ADR | Código | Pruebas | Evidencia |
|---|---|---|---|---|---|---|---|
| A-01 | Captura inteligente de información académica | RF-01 | Pendiente | [ADR-0001](adr/0001-estilo-arquitectonico.md) | Pendiente | Pendiente | Pendiente |

## Descripción del aspecto A-01

**Nombre:** Captura inteligente de información académica

**Usuario:** Estudiante universitario

**Problema que resuelve:** Permite al estudiante registrar información académica mediante mensajes en lenguaje natural enviados al bot de Telegram, evitando la necesidad de abrir la aplicación móvil y completar formularios manualmente.

**Resultado esperado:** El sistema interpreta el mensaje mediante Gemini, identifica la intención y transforma la información en datos estructurados. El backend valida la información y la almacena en PostgreSQL para que pueda ser consultada y gestionada posteriormente desde la aplicación Flutter.

## Escenario de calidad relacionado

[S1 — Registro correcto de información académica](calidad/escenarios_calidad.md#escenario-1--registro-correcto-de-información-académica)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

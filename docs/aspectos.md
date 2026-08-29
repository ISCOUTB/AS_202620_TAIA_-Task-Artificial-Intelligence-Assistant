# Aspectos del sistema

| ID | Aspecto | Requisito | C4 | ADR | Código | Pruebas | Evidencia |
|---|---|---|---|---|---|---|---|
| A-01 | Captura inteligente de información académica | RF-01, RF-02 | [C4-C1](c4/C4-C1.md), [C4-C2](c4/C4-C2.md) | [ADR-0001](adr/0001-estilo-arquitectonico.md) | [`backend/app/modules/academic/`](../backend/app/modules/academic/) | [`test_academic_task_domain.py`](../backend/tests/test_academic_task_domain.py), [`test_academic_register_task.py`](../backend/tests/test_academic_register_task.py) | Pendiente |

## Descripción del aspecto A-01

**Nombre:** Captura inteligente de información académica

**Usuario:** Estudiante universitario

**Problema que resuelve:** Permite al estudiante registrar información académica mediante mensajes en lenguaje natural enviados al bot de Telegram, evitando la necesidad de abrir la aplicación móvil y completar formularios manualmente.

**Resultado esperado:** El sistema interpreta el mensaje mediante Gemini, identifica la intención y transforma la información en datos estructurados. El backend valida la información y la almacena en PostgreSQL para que pueda ser consultada y gestionada posteriormente desde la aplicación Flutter.

**Estado de la implementación:** este incremento entrega un **corte vertical parcial** de A-01: registro y consulta de tareas académicas mediante HTTP (`POST /academic/tasks`, `GET /academic/tasks`), con un adaptador de persistencia en memoria. La interpretación mediante Gemini y el canal de Telegram, así como el adaptador de PostgreSQL, quedan como trabajo pendiente para entregas posteriores; el diseño hexagonal del módulo permite incorporarlos sustituyendo adaptadores sin modificar el dominio ni los casos de uso.

## Escenario de calidad relacionado

[S1 — Registro correcto de información académica](calidad/escenarios_calidad.md#escenario-1--registro-correcto-de-información-académica)

## Decisión arquitectónica relacionada

[ADR-0001 — Monolito modular con organización hexagonal selectiva](adr/0001-estilo-arquitectonico.md)

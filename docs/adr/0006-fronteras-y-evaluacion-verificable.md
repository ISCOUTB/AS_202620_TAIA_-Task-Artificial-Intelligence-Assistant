# ADR-0006 — Contratos de consulta y composición de casos de uso

## Estado

Aceptado por el equipo el 2026-10-05, tras revisar la propuesta redactada con
apoyo de IA (ver [ia.md, entradas 015 y 016](../ia.md)). La aceptación
corresponde a la decisión descrita; no implica que los cambios estén
desplegados.

## Contexto

La [auditoría S8](../auditoria_erosion.md) dejó E-02 y E-05 abiertos:
los controladores elegían repositorios y AI importaba el estado de tarea del
dominio de Academic. El contrato HTTP versionado debe conservarse y las
consultas deben seguir limitadas al propietario. No se añaden dependencias.

## Escenario de calidad relacionado

**S4 — Acceso únicamente a datos del propio estudiante:** Academic conserva
la validación del propietario al traducir los filtros.

**S5 — Sustitución del modelo de IA:** los consumidores dependen de contratos
de aplicación y la composición de implementaciones queda fuera del transporte.
Esta decisión facilita la sustitución, pero no sustituye su prueba de aceptación.

## Opciones consideradas

### Opción A — Mantener las excepciones de la línea base

Conserva el acoplamiento observado y permite que reaparezca sin romper CI.

### Opción B — Reexportar el enum de Academic

Evita el import directo, pero mantiene expuesto el vocabulario interno y no
resuelve quién traduce los filtros producidos por el modelo.

### Opción C — Contrato público e inyección desde la composición

Academic publica filtros de texto y los traduce internamente. Los controladores
reciben casos de uso ya construidos. Mantiene la interfaz HTTP y permite probar
las fronteras sin depender de un proveedor o una base remota.

## Decisión

Se adopta la **Opción C**.

Se introduce `AcademicTaskQuery`, un DTO público con filtros de texto.
Academic traduce los estados y conserva su validación y control de propiedad.
AI consume únicamente el puerto de entrada. El servicio acepta también
`TaskQuery` para conservar los consumidores internos existentes.

`main.py` construye e inyecta los casos de uso de estructura académica y
recordatorios. Los controladores conservan sus funciones `Depends`, por lo
que los overrides existentes siguen funcionando. Son casos de uso sin estado
por petición; los repositorios administran sus sesiones por operación.

## Consecuencias

### Positivas

La construcción pasa al arranque y una dependencia ausente falla explícitamente.
La línea base de fronteras queda vacía; las excepciones corregidas ya no pueden
reaparecer como aceptadas. Las pruebas de filtros conservan los alias y verifican
que otro usuario no pueda leer las tareas.

### Negativas

El arranque debe configurar todos los casos de uso antes de atender peticiones.
Las instancias compartidas no deben guardar estado mutable por usuario.
Se conserva temporalmente la compatibilidad con `TaskQuery` para los
consumidores internos de Academic.

## Verificación

[Procedimiento rojo/verde y resultados](../cierre_matriz_local.md).
El contrato OpenAPI conserva sus cuatro pruebas aprobadas. Las pruebas de
integración con PostgreSQL requieren una base de pruebas aislada.

# ADR-0002 — Integración HTTP síncrona con contrato OpenAPI

## Estado

Aceptado.

## Contexto

TAIA expone una API HTTP principal consumida por la aplicación cliente y utilizada para las operaciones de Usuario, Academic, AI y Reminders. En el estado actual del proyecto, estas operaciones son de consulta, registro y actualización y requieren una respuesta inmediata para que el cliente conozca el resultado de la operación.

La Semana 7 exige formalizar el contrato de esta integración, generar un cliente o stub y comprobar mediante una prueba de contrato que un cambio incompatible sea detectable.

## Escenario de calidad relacionado

La decisión se relaciona principalmente con **S1 — Registro correcto de información académica**, **S3 — Respuesta del asistente ante un mensaje** y **S4 — Acceso únicamente a datos del propio estudiante**: el consumidor necesita una respuesta HTTP explícita para conocer si una operación fue aceptada, rechazada por validación o rechazada por autorización/pertenencia.

## Opciones consideradas

### Opción A — HTTP síncrono + JSON + OpenAPI

El cliente realiza una solicitud HTTP y espera una respuesta HTTP con un cuerpo JSON cuando corresponde. La interfaz pública se versiona en `docs/api/openapi.json` y se usa como contrato verificable.

### Opción B — Integración asíncrona mediante mensajería/eventos

El cliente publicaría eventos y el resultado se procesaría posteriormente mediante un mecanismo de mensajería. Esto sería útil para flujos desacoplados y procesamiento diferido, pero introduciría infraestructura adicional y cambiaría el modelo de interacción de las operaciones CRUD y de consulta actuales.

### Opción C — HTTP sin contrato formal

La API continuaría siendo síncrona, pero el consumidor dependería de la implementación o de documentación informal. Se descarta porque no permite detectar de forma sistemática una incompatibilidad entre proveedor y consumidor.

## Decisión

TAIA utilizará **HTTP síncrono con JSON** como estrategia de integración de la API principal y **OpenAPI 3.1** como contrato versionado de la interfaz.

La API se identifica actualmente como versión `1.0.0`. El contrato se almacena en `docs/api/openapi.json`. Los cambios incompatibles de la superficie HTTP deben producir una actualización de versión y una modificación coordinada del contrato y del cliente generado.

La prueba `backend/tests/test_api_contract.py` compara la superficie declarada en OpenAPI con la aplicación FastAPI y contiene una comprobación explícita de que una modificación incompatible es detectada.

## Consecuencias

### Positivas

- El consumidor dispone de una interfaz ejecutable y versionada.
- Los cambios de rutas, métodos o esquemas pueden detectarse antes de integrar.
- El contrato puede alimentar herramientas de documentación, pruebas y generación de cliente.
- La comunicación HTTP/JSON es compatible con los consumidores actuales de TAIA.

### Negativas

- El contrato debe mantenerse sincronizado con la implementación.
- Los cambios incompatibles requieren coordinación y versionado.
- La prueba de contrato no sustituye las pruebas funcionales de cada módulo.
- La integración síncrona mantiene al consumidor esperando una respuesta cuando intervienen dependencias externas como Gemini.

## Trazabilidad

- **S7:** Contrato de API y prueba de contrato.
- **Contrato:** [`docs/api/openapi.json`](../../docs/api/openapi.json)
- **Prueba:** [`backend/tests/test_api_contract.py`](../../backend/tests/test_api_contract.py)
- **Cliente generado:** [`backend/generated/taia_api_client.py`](../../backend/generated/taia_api_client.py)
- **Generador:** [`tools/generate_api_client.py`](../../tools/generate_api_client.py)
- **CI:** [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)
- **C4 nivel 2:** [`docs/c4/C4-C2.md`](../c4/C4-C2.md)
- **arc42 sección 6:** [`docs/arc42/06-vista-de-ejecucion.md`](../arc42/06-vista-de-ejecucion.md)

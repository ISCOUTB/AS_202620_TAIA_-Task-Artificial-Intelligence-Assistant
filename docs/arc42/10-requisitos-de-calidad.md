# 10. Requisitos de calidad

Los requisitos de calidad de TAIA se expresan mediante escenarios medibles. Estos escenarios permiten evaluar el comportamiento esperado del sistema y sirven como referencia para las decisiones arquitectónicas y las pruebas.

## 10.1. Árbol de calidad

La utilidad del sistema se descompone en las siguientes características de calidad:

```text
UTILIDAD
│
├── Exactitud
│   │
│   └── Interpretación correcta de información académica
│       │
│       └── S1. Registro correcto de información académica
│
├── Disponibilidad / Puntualidad
│   │
│   └── Entrega oportuna de información
│       │
│       └── S2. Entrega puntual de recordatorios
│
├── Rendimiento
│   │
│   └── Tiempo de respuesta del asistente
│       │
│       └── S3. Respuesta del asistente ante un mensaje
│
├── Seguridad
│   │
│   └── Confidencialidad y aislamiento de información
│       │
│       └── S4. Acceso únicamente a datos del propio estudiante
│
└── Mantenibilidad
    │
    └── Independencia del proveedor de IA
        │
        └── S5. Sustitución del modelo de IA
```

## 10.2. Escenarios de calidad

### S1 — Registro correcto de información académica

**Fuente:** El estudiante.

**Estímulo:** Escribe en lenguaje natural información correspondiente a una tarea, examen, materia o clase/evento.

**Artefacto:** Servicio que interpreta el mensaje con el LLM y registro de TAIA.

**Entorno:** Sistema desplegado, con el servicio de IA disponible.

**Respuesta:** TAIA identifica los campos relevantes, solicita confirmación cuando corresponda y registra la información correctamente en PostgreSQL.

**Medida:** Al menos el 90 % de los campos esperados deben ser identificados y registrados correctamente en una muestra de 100 mensajes académicos representativos.

**Restricción relacionada:** El contexto enviado al LLM debe mantenerse controlado debido a las cuotas gratuitas disponibles.

**Justificación:** La captura sin fricción es una característica diferenciadora de TAIA. Una baja exactitud en la interpretación reduciría la confianza del estudiante en el sistema.

### S2 — Entrega puntual de recordatorios

**Fuente:** Sistema de TAIA.

**Estímulo:** Llega el momento programado para un recordatorio.

**Artefacto:** Servicio de recordatorios y notificaciones.

**Entorno:** Sistema desplegado y operativo.

**Respuesta:** TAIA envía el recordatorio al canal configurado por el estudiante.

**Medida:** Al menos el 95 % de los recordatorios deben ser entregados dentro de un margen de ±1 minuto respecto a la hora programada, en una prueba de 100 recordatorios.

**Justificación:** Los recordatorios solo son útiles si se entregan en el momento esperado por el estudiante.

### S3 — Respuesta del asistente ante un mensaje

**Fuente:** El estudiante.

**Estímulo:** El estudiante envía una consulta o instrucción válida al asistente de TAIA.

**Artefacto:** Backend de TAIA y servicio de interpretación mediante LLM.

**Entorno:** Sistema desplegado, con backend, Telegram y servicio de IA disponibles.

**Respuesta:** TAIA procesa el mensaje y devuelve una respuesta al estudiante.

**Medida:** El 95 % de las solicitudes deberá recibir una respuesta en un tiempo ≤ 7 segundos, medido desde la recepción del mensaje por el backend hasta el envío de la respuesta al canal del estudiante, bajo condiciones normales de operación.

**Restricción relacionada:** El sistema utiliza infraestructura gratuita, sin garantía de recursos dedicados, por lo que pueden existir arranques en frío y recursos compartidos.

**Justificación:** Un tiempo de respuesta excesivo afecta la usabilidad del asistente y puede perjudicar los escenarios de registro y consulta.

### S4 — Acceso únicamente a datos del propio estudiante

**Fuente:** El estudiante autenticado.

**Estímulo:** Envía un mensaje solicitando, directa o indirectamente, información perteneciente a otro estudiante.

**Artefacto:** Capa que construye el contexto para el LLM y mecanismo de persistencia.

**Entorno:** Sistema desplegado con múltiples estudiantes registrados.

**Respuesta:** TAIA devuelve únicamente información asociada al estudiante autenticado y rechaza cualquier intento de acceder a información perteneciente a otro estudiante.

**Medida:** En una prueba de 100 intentos de acceso, incluyendo solicitudes legítimas y solicitudes que intenten consultar información perteneciente a otros estudiantes, el sistema deberá permitir únicamente los accesos autorizados y rechazar el 100 % de los intentos no autorizados, sin exponer datos de otros usuarios.

**Restricción relacionada:** El uso de un LLM con contexto generado para cada petición exige controlar explícitamente el aislamiento de los datos.

**Justificación:** TAIA manejará información académica de estudiantes. Una fuga de información entre usuarios afectaría gravemente la seguridad y la confianza en el sistema.

### S5 — Sustitución del modelo de IA

**Fuente:** El equipo de desarrollo.

**Estímulo:** El proveedor o modelo de inteligencia artificial utilizado por TAIA deja de estar disponible, cambia sus condiciones de uso o se requiere migrar a otro proveedor.

**Artefacto:** Componente de integración con el LLM.

**Entorno:** Durante el mantenimiento y evolución del sistema.

**Respuesta:** El sistema debe permitir sustituir el proveedor de IA mediante el cambio o incorporación del adaptador correspondiente, manteniendo sin modificaciones las reglas de negocio y la interfaz utilizada por la aplicación.

**Medida:** La sustitución del proveedor de IA deberá requerir cambios en máximo 2 archivos del adaptador, sin modificar archivos pertenecientes al dominio ni a las reglas de negocio.

**Restricción relacionada:** El proveedor de LLM debe ser intercambiable.

**Justificación:** Los proveedores pueden modificar sus modelos, cuotas o condiciones de uso. El aislamiento del proveedor evita que un cambio de infraestructura obligue a modificar la lógica de negocio de TAIA.

## 10.3. Priorización de escenarios

| Escenario                      | Impacto | Riesgo técnico | Prioridad |
| ------------------------------ | ------- | -------------- | --------- |
| S1 — Registro correcto         | Alto    | Alto           | Alta      |
| S2 — Recordatorios puntuales   | Alto    | Alto           | Alta      |
| S3 — Respuesta del asistente   | Alto    | Media/Alta     | Alta      |
| S4 — Aislamiento de datos      | Alto    | Crítico        | Crítica   |
| S5 — Sustitución del modelo IA | Medio   | Medio          | Media     |

## 10.4. Relación con las decisiones arquitectónicas

Los escenarios de calidad sirven como fundamento para las decisiones arquitectónicas de TAIA.

En particular:

* **S1** influye en la separación entre interpretación, validación y reglas de dominio.
* **S2** influye en la separación del mecanismo de notificaciones respecto de la lógica de negocio.
* **S3** establece un objetivo de rendimiento condicionado por el uso de servicios externos y la infraestructura disponible.
* **S4** exige mantener el aislamiento de la información de cada estudiante y controlar el contexto utilizado por el sistema.
* **S5** motiva directamente el **ADR-0001**, que establece el uso de puertos y adaptadores para aislar las dependencias externas.

**ADR relacionado:** [ADR-0001 — Monolito modular con organización hexagonal selectiva](../adr/0001-estilo-arquitectonico.md)

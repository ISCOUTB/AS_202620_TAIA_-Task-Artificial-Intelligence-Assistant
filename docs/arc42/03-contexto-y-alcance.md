# 3. Contexto y alcance

## 3.1. Contexto de negocio
TAIA se sitúa entre el estudiante y los servicios necesarios para gestionar su información académica.

El estudiante utiliza TAIA para **registrar y consultar información académica**, así como para **recibir recordatorios**. TAIA interpreta las solicitudes expresadas en lenguaje natural, procesa las operaciones correspondientes y mantiene la información asociada al estudiante.

### Intercambio principal

```text
+------------------+
|    Estudiante    |
+--------+---------+
         |
         | registra / consulta información
         | y recibe recordatorios
         v
+--------------------------+
|           TAIA           |
| Task Artificial          |
| Intelligence Assistant   |
+-----------+--------------+
            |
            | interpretación de lenguaje natural
            v
+--------------------------+
| Servicio de IA (Gemini)  |
+--------------------------+

TAIA <----> Telegram
        mensajes y recordatorios
```

### Interfaces externas del contexto de negocio

| Sistema / Actor | Relación con TAIA |
|---|---|
| **Estudiante** | Utiliza TAIA para registrar y consultar información académica y recibir recordatorios. |
| **Telegram** | Proporciona un canal conversacional para recibir mensajes del estudiante y enviar respuestas y recordatorios. |
| **Servicio de IA (Gemini)** | Proporciona la interpretación de solicitudes expresadas mediante lenguaje natural. |

---

## 3.2. Contexto técnico

TAIA se integra con servicios externos mediante interfaces tecnológicas específicas. El backend actúa como punto central de procesamiento y validación de las solicitudes.

### Interfaces técnicas

| Sistema / Interfaz | Tecnología / Canal | Propósito |
|---|---|---|
| **Aplicación cliente** | Flutter / HTTP | Permitir al estudiante interactuar con las funcionalidades de TAIA. |
| **Telegram** | Telegram Bot API / Webhook | Recibir mensajes del estudiante y enviar respuestas y recordatorios. |
| **Servicio de IA** | API de Gemini / HTTP | Interpretar solicitudes expresadas en lenguaje natural y producir información estructurada para su posterior validación. |
| **Persistencia** | PostgreSQL / conexión de base de datos | Almacenar y consultar la información académica gestionada por TAIA. |

### Flujo técnico principal

```text
                         Estudiante
                         /        \
                        /          \
                       v            v
                   Flutter       Telegram
                       |            |
                       |            |
                       +-----+------+
                             |
                             | HTTP / Webhook
                             v
                      +-------------+
                      |   FastAPI   |
                      |   Backend   |
                      +------+------+
                             |
                   +---------+---------+
                   |                   |
                   v                   v
              Gemini API          PostgreSQL
                   |
                   v
          Interpretación
           estructurada
                   |
                   v
        Validación y reglas
          de negocio en TAIA
```

> **Nota:** El servicio de IA se utiliza únicamente como mecanismo de interpretación y **no está autorizado para acceder directamente a la persistencia**.

---

| Entrada / Salida | Canal | Uso |
|---|---|---|
| **Mensaje del estudiante** | Telegram Bot API | Entrada de solicitudes expresadas en lenguaje natural. |
| **Solicitud desde la aplicación** | HTTP hacia FastAPI | Entrada de operaciones académicas desde el cliente Flutter. |
| **Respuesta del asistente** | Telegram / aplicación cliente | Confirmación, resultado de una operación o respuesta a una consulta. |
| **Recordatorio académico** | Telegram y/o canal configurado | Entrega de información asociada a un evento programado. |
| **Información estructurada generada por IA** | API de Gemini → FastAPI | Resultado de interpretación que debe ser validado antes de utilizarse. |
| **Datos académicos persistidos** | PostgreSQL | Almacenamiento y consulta de la información gestionada por TAIA. |

---

### 3.2.1. Estado de la línea base ejecutable

La línea base implementada actualmente se concentra en el backend FastAPI. Los módulos disponibles son `usuario`, `academic`, `ai` y `reminders`. El cliente Flutter y PostgreSQL forman parte de la arquitectura objetivo, pero no están presentes como componentes ejecutables en esta línea base.

El backend dispone de autenticación JWT, aislamiento por usuario, CRUD de tareas, flujo de asistente mediante `/ai/message`, CRUD de recordatorios y envío explícito de notificaciones por Telegram. La integración con Gemini está encapsulada detrás de un puerto y requiere configuración del proveedor para su ejecución real.

## 3.3. Alcance

El alcance del **MVP de TAIA** comprende la gestión de información académica básica:

- **Tareas**
- **Exámenes**
- **Materias**
- **Clases y eventos**
- Interacción mediante **lenguaje natural**
- Consulta de **información propia**
- Generación y entrega de **recordatorios**

### Fuera del alcance del MVP

Las capacidades avanzadas de inteligencia artificial quedan fuera del alcance de esta primera versión. Entre ellas se encuentran:

- RAG (*Retrieval-Augmented Generation*)
- Embeddings
- Búsqueda semántica
- Otras extensiones avanzadas de IA

Estas capacidades podrán incorporarse en **etapas posteriores** del proyecto.

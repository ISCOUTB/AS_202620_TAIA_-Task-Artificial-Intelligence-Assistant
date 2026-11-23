# 3. Contexto y alcance

## 3.1. Contexto de negocio
TAIA se sitúa entre el estudiante y los servicios necesarios para gestionar su información académica.

El estudiante utiliza TAIA para **registrar y consultar información académica**, así como para **recibir recordatorios**. TAIA interpreta las solicitudes expresadas en lenguaje natural, procesa las operaciones correspondientes y mantiene la información asociada al estudiante.

### Intercambio principal

```text
                  +------------------+
                  |    Estudiante    |
                  +---+----------+---+
      app móvil       |          |      bot de Telegram
                      v          v
                  +------------------+          +---------------------------+
                  |       TAIA       |<-------->| Proveedores LLM           |
                  | Task Artificial  |          | Groq (principal),         |
                  | Intelligence     |          | Gemini (respaldo)         |
                  | Assistant        |          +---------------------------+
                  +---+----------+---+
                      |          |
                      v          v
      +---------------------+  +-----------------------------+
      | Firebase Cloud      |  | Resend                      |
      | Messaging (push)    |  | (correo de recuperación)    |
      +---------------------+  +-----------------------------+
```

### Interfaces externas del contexto de negocio

| Sistema / Actor | Relación con TAIA |
|---|---|
| **Estudiante** | Registra y consulta su información académica desde la app, conversa con el asistente desde la app o desde Telegram y recibe recordatorios en el teléfono. |
| **Telegram** | Canal conversacional: el estudiante vincula su cuenta y conversa con el asistente. No entrega recordatorios (D-10). |
| **Proveedores LLM** | Groq, y Gemini como respaldo, interpretan las solicitudes en lenguaje natural ([ADR-0013](../adr/0013-usar-groq-como-proveedor-llm-principal.md)). |
| **Firebase Cloud Messaging** | Único canal de las notificaciones push (D-10, [ADR-0012](../adr/0012-enviar-recordatorios-con-un-proceso-dentro-de-la-api.md)). |
| **Resend** | Envía el código de recuperación de contraseña (RF-USR-08). |

---

## 3.2. Contexto técnico

TAIA se integra con servicios externos mediante interfaces tecnológicas específicas. El backend actúa como punto central de procesamiento y validación de las solicitudes.

### Interfaces técnicas

| Sistema / Interfaz | Tecnología / Canal | Propósito |
|---|---|---|
| **App móvil** | Flutter / HTTPS con JWT | Todas las funciones del estudiante, incluido el chat con el asistente (`POST /ai/message`). |
| **Telegram** | Webhook con secreto (`POST /telegram/webhook`) | Recibir los mensajes del bot. La respuesta viaja en el cuerpo de la respuesta del webhook. |
| **Proveedores LLM** | API de Groq y API de Gemini / HTTPS | Interpretar el mensaje y producir información estructurada que TAIA valida antes de usar. |
| **Firebase Cloud Messaging** | Firebase Admin SDK / HTTPS | Enviar los recordatorios vencidos a los dispositivos registrados. |
| **Resend** | API de Resend / HTTPS | Enviar el correo de recuperación de contraseña. |
| **Persistencia** | PostgreSQL (Supabase) / SQL | Almacenar la información de los cuatro módulos. |

### Flujo técnico principal

```text
                         Estudiante
                         /                                v          v
                   App móvil     Telegram
                        |            |
            HTTPS + JWT |            | webhook con secreto
                        +-----+------+
                              v
                      +---------------+        +-----------------+
                      |  API FastAPI  |------->| Groq -> Gemini  |
                      |  (monolito    |<-------| interpretación  |
                      |   modular)    |        +-----------------+
                      +--+---------+--+
                         |         |
                         v         v
                    PostgreSQL   Bucle de envío (cada 60 s)
                                   |
                                   v
                         Firebase Cloud Messaging
                                   |
                                   v
                              App móvil
```

> **Nota:** el proveedor LLM se usa solo para interpretar. No recibe identificadores de usuario, no accede a la persistencia y ningún identificador que produzca se usa para acceder a datos.

---

| Entrada / Salida | Canal | Uso |
|---|---|---|
| **Mensaje del estudiante** | App (`POST /ai/message`) o Telegram (webhook) | Solicitudes en lenguaje natural. |
| **Solicitud desde la aplicación** | HTTPS hacia FastAPI | Operaciones académicas desde el cliente Flutter. |
| **Respuesta del asistente** | App o Telegram | Confirmación, resultado de una operación o respuesta a una consulta. |
| **Recordatorio académico** | Firebase Cloud Messaging y bandeja de la app | Aviso de una actividad cuando llega la hora programada. |
| **Información estructurada generada por IA** | Groq o Gemini → FastAPI | Resultado de interpretación que se valida antes de utilizarse. |
| **Datos académicos persistidos** | PostgreSQL | Almacenamiento y consulta de la información gestionada por TAIA. |

---

### 3.2.1. Estado del sistema entregado

El backend FastAPI está desplegado con los módulos `usuario`, `academic`, `ai` y `reminders` sobre PostgreSQL, y la app Flutter se conecta a él. El backend ofrece autenticación JWT, aislamiento por usuario, asignaturas, horario, actividades, calendario, plan de estudio, recordatorios con envío automático por FCM, bandeja de notificaciones y el asistente por la app y por Telegram. Lo que no se terminó está declarado en los estados de [requerimientos.md](../requerimientos.md).

## 3.3. Alcance

El alcance del **MVP de TAIA** comprende la gestión de información académica básica:

- **Tareas**
- **Exámenes**
- **Materias**
- **Clases y eventos**
- Interacción mediante **lenguaje natural**, desde la app y desde Telegram
- Consulta de **información propia**
- Generación y entrega de **recordatorios** por notificación push
- **Plan de estudio** sugerido a partir de las preferencias del estudiante

### Fuera del alcance del MVP

Las capacidades avanzadas de inteligencia artificial quedan fuera del alcance de esta primera versión. Entre ellas se encuentran:

- RAG (*Retrieval-Augmented Generation*)
- Embeddings
- Búsqueda semántica
- Otras extensiones avanzadas de IA

Estas capacidades podrán incorporarse en **etapas posteriores** del proyecto. El resto de lo que queda fuera del MVP, como las notificaciones por Telegram, correo o SMS, está en la sección 13 de [requerimientos.md](../requerimientos.md).

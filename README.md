# TAIA - Task Artificial Intelligence Assistant

Sistema de gestión académica para estudiantes universitarios, apoyado por inteligencia artificial y comunicación mediante lenguaje natural.

## Integrantes

- Valeria Berrio Payares
- Deiner Gonzales Paredes
- Luis Mendoza Angulo
- Mark Pastrana Koreia 

## Descripción

El Asistente Académico Inteligente busca facilitar la organización de la vida académica de los estudiantes universitarios mediante una interfaz móvil y un bot de Telegram.

El estudiante podrá registrar información académica utilizando mensajes en lenguaje natural. Por ejemplo:

> "Tengo que entregar el proyecto de programación el próximo lunes."

El sistema utilizará Gemini para interpretar el mensaje, identificar la intención y transformar la información en datos estructurados. Posteriormente, el backend validará la información y la almacenará en PostgreSQL.

La información registrada podrá ser consultada y gestionada desde la aplicación desarrollada en Flutter.

## Funcionalidades del MVP

- Gestión de materias.
- Registro de tareas.
- Registro de exámenes.
- Calendario académico.
- Recordatorios.
- Dashboard académico.
- Captura de información mediante Telegram.
- Interpretación de lenguaje natural mediante Gemini.

## Tecnologías

- **Flutter:** aplicación móvil.
- **FastAPI:** backend y API del sistema.
- **PostgreSQL:** almacenamiento de información académica.
- **Gemini:** interpretación de lenguaje natural y asistencia conversacional.
- **Telegram Bot API:** canal de captura rápida de información.

## Estado actual

El proyecto evolucionó desde el esqueleto arquitectónico inicial hacia un backend ejecutable con los módulos **Usuario, Academic, Reminders y AI**. La línea base actual mantiene un **monolito modular con organización hexagonal selectiva**, y cuenta con autenticación, aislamiento por usuario, gestión de tareas académicas, gestión de recordatorios y un flujo de asistente preparado para conectarse con un proveedor LLM.

### Funcionalidad actualmente implementada

- **Usuario:** registro, login mediante JWT, consulta del usuario autenticado y vinculación de una cuenta de Telegram.
- **Academic:** registro, consulta, actualización y completado de tareas; las operaciones están asociadas al usuario autenticado.
- **AI:** endpoint autenticado `/ai/message`, conversaciones en memoria, confirmación de operaciones y un puerto de integración con LLM; existe adaptador para Gemini, pero la credencial/configuración del proveedor todavía debe habilitarse para ejecutar el flujo contra Gemini real.
- **Reminders:** creación, consulta, edición, eliminación y completado de recordatorios; asociación con tareas Academic; aislamiento por usuario.
- **Notificaciones:** generación y envío explícito de una notificación mediante Telegram cuando existe una cuenta vinculada y `TAIA_TELEGRAM_BOT_TOKEN` está configurado.
- **Persistencia:** la línea base ejecutable utiliza repositorios en memoria. PostgreSQL sigue siendo parte de la arquitectura objetivo y no está integrado todavía.

### Estado de las integraciones externas

| Integración | Estado | Observación |
|---|---|---|
| Telegram | Parcialmente implementada | Vinculación de cuenta y envío de notificaciones implementados; el envío requiere configuración del bot. |
| Gemini | Preparada | Existe puerto/adaptador y manejo de configuración; falta habilitar la credencial para probar el proveedor real. |
| PostgreSQL | Pendiente | Los repositorios actuales de Academic y Reminders son en memoria. |
| Flutter | Arquitectura objetivo | No forma parte del backend entregado en esta línea base. |

### Evidencia de pruebas

La suite automatizada actual contiene pruebas de dominio, casos de uso, API, autenticación, aislamiento de usuarios, integración AI-Academic y Reminders/Telegram. En la línea base documentada se verificó:

```text
74 passed
```



### Recorridos funcionales de la línea base

**Academic**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/academic/tasks` | Registra una tarea del usuario autenticado. |
| `GET` | `/academic/tasks` | Lista las tareas del usuario autenticado. |
| `PATCH` | `/academic/tasks/{task_id}` | Actualiza una tarea propia. |
| `PATCH` | `/academic/tasks/{task_id}/complete` | Marca una tarea propia como completada. |

**Usuario**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/users` | Registra un usuario. |
| `POST` | `/users/login` | Obtiene un JWT. |
| `GET` | `/users/me` | Consulta el usuario autenticado. |
| `POST` | `/users/me/telegram/link` | Genera un enlace temporal de vinculación con Telegram. |
| `POST` | `/users/telegram/link/confirm` | Confirma la vinculación de Telegram. |

**AI**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/ai/message` | Procesa un mensaje del asistente para el usuario autenticado. |

**Reminders**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/reminders` | Crea un recordatorio asociado a una tarea Academic. |
| `GET` | `/reminders` | Lista los recordatorios propios. |
| `GET` | `/reminders/{reminder_id}` | Consulta un recordatorio propio. |
| `PATCH` | `/reminders/{reminder_id}` | Edita un recordatorio propio. |
| `POST` | `/reminders/{reminder_id}/complete` | Marca un recordatorio como completado. |
| `DELETE` | `/reminders/{reminder_id}` | Elimina un recordatorio propio. |
| `POST` | `/reminders/{reminder_id}/notify` | Genera y envía explícitamente una notificación por Telegram. |

### Recorrido representativo

```text
JWT
 ↓
POST /academic/tasks
 ↓
TaskRepository (memoria)

JWT
 ↓
POST /reminders
 ↓
validación de tarea Academic
 ↓
ReminderRepository (memoria)
 ↓
POST /reminders/{id}/notify
 ↓
Telegram Bot API
```

El flujo `/ai/message` utiliza un puerto LLM y un `AcademicGateway` para traducir las operaciones del asistente hacia el módulo Academic. El adaptador Gemini está preparado, pero requiere configuración de la credencial del proveedor.

## Arquitectura

TAIA adopta un **monolito modular con organización hexagonal selectiva** en los módulos que presentan dependencias externas relevantes.

El backend actual se organiza en los siguientes módulos:

- `usuario`: identidad, JWT y vinculación con Telegram.
- `academic`: tareas académicas y reglas de dominio.
- `reminders`: recordatorios y notificaciones.
- `ai`: conversaciones y abstracción del proveedor LLM.

Los módulos contemplan las siguientes responsabilidades arquitectónicas:

- `domain`: reglas y conceptos propios del módulo.
- `application`: casos de uso y coordinación de la lógica.
- `adapters`: integración con tecnologías y servicios externos.

La decisión arquitectónica está documentada en:

[ADR-0001 — Estilo arquitectónico](docs/adr/0001-estilo-arquitectonico.md)

## Documentación

La documentación del proyecto se encuentra en la carpeta docs/.

- docs/ficha_problema.md — descripción del problema y propuesta de solución.
- docs/aspectos.md — aspectos arquitectónicos y trazabilidad.
- docs/ia.md — registro del uso de inteligencia artificial.
- docs/arc42/ — documentación de arquitectura mediante arc42.
- docs/c4/ — diagramas de arquitectura C4.
- docs/calidad/ — atributos y escenarios de calidad.
- docs/adr/ — decisiones arquitectónicas.

## Requisitos

Para ejecutar el proyecto se requiere:

Python 3.14 o compatible.
Las dependencias especificadas en backend/requirements.txt.

### Instalar las dependencias:

pip install -r backend/requirements.txt

### Ejecución

El proyecto cuenta con un backend ejecutable del monolito modular.

Desde la raíz del repositorio, ejecutar:

.\run.bat

El servidor se iniciará en:

http://127.0.0.1:8000

Health check
Para comprobar que el backend está funcionando:

GET /health

También puede accederse desde el navegador:

http://127.0.0.1:8000/health

Respuesta esperada:

{
  "status": "ok"
}

La documentación interactiva de FastAPI está disponible en:

http://127.0.0.1:8000/docs

### Pruebas

Las pruebas automatizadas se ejecutan desde la raíz del repositorio con:

pytest backend/tests

Las pruebas cubren:

- reglas y casos de uso del módulo Academic;
- autenticación y aislamiento de usuarios;
- flujo AI y su integración con Academic;
- API y casos de uso de Reminders;
- notificaciones y endpoint de Telegram.

Las principales evidencias se encuentran en `backend/tests/`, incluyendo:

- `test_academic_register_task.py`
- `test_academic_update_task.py`
- `test_academic_user_isolation.py`
- `test_ai_api.py`
- `test_ai_academic_gateway.py`
- `test_reminders_api.py`
- `test_reminders_notifications.py`
- `test_reminders_notify_api.py`


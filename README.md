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

## Estado

El proyecto avanza de la etapa de esqueleto arquitectónico (Entrega 3) a un primer **corte vertical ejecutable** correspondiente al aspecto **A-01 — Captura inteligente de información académica** (RF-01, RF-02).

Este incremento implementa el registro y la consulta de tareas académicas, atravesando las tres capas del módulo `academic` definidas en ADR-0001: `domain`, `application` y `adapters`. Es un corte **parcial**: expone el registro de tareas mediante HTTP con un adaptador de persistencia en memoria, en lugar del flujo completo Telegram → Gemini → PostgreSQL descrito en `docs/ficha_problema.md`. La interpretación con Gemini, el canal de Telegram y la persistencia en PostgreSQL se incorporarán en entregas posteriores sustituyendo únicamente los adaptadores correspondientes, sin modificar el dominio ni los casos de uso.


### Corte vertical: registro de tareas (A-01)

**Alcance de este incremento**

- `domain/task.py`: entidad `Task` y las reglas de validación mínimas (título obligatorio, longitud máxima).
- `application/register_task.py` y `application/list_tasks.py`: casos de uso que orquestan la creación y la consulta de tareas contra el puerto `TaskRepository`.
- `application/ports.py`: puerto `TaskRepository`, la interfaz que aísla la aplicación de la tecnología de persistencia concreta.
- `adapters/in_memory_task_repository.py`: adaptador de persistencia **en memoria**, temporal. Se sustituirá por un adaptador de PostgreSQL sin tocar el dominio ni la aplicación.
- `adapters/api.py`: adaptador de entrada HTTP (router de FastAPI) que expone los endpoints y traduce entre esquemas Pydantic y entidades de dominio.

**Endpoints**

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/academic/tasks` | Registra una tarea académica (RF-01). |
| `GET` | `/academic/tasks` | Lista las tareas registradas (RF-02). |

**Ejemplo de uso**

```bash
curl -X POST http://127.0.0.1:8000/academic/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Entregar proyecto de programación", "due_date": "2026-09-07", "subject": "Programación"}'
```

Respuesta esperada:

```json
{
  "id": "a24a243a-5931-465a-8303-f32153832d10",
  "title": "Entregar proyecto de programación",
  "due_date": "2026-09-07",
  "subject": "Programación",
  "description": null,
  "status": "pending"
}
```

```bash
curl http://127.0.0.1:8000/academic/tasks
```

## Arquitectura

TAIA adopta un **monolito modular con organización hexagonal selectiva** en los módulos que presentan dependencias externas relevantes.

La estructura inicial del backend se organiza en los siguientes módulos:

- `academic`: información académica.
- `reminders`: gestión de recordatorios.
- `ai`: integración con servicios de inteligencia artificial.

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

El proyecto cuenta con un esqueleto ejecutable del backend.

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

- reglas del dominio de tareas;
- caso de uso de registro y consulta de tareas;
- comprobación del estado del backend.

El corte vertical A-01 se verifica mediante:

backend/tests/test_academic_register_task.py


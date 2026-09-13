# Propiedad de datos — S6

La propiedad de datos se define por módulo. Cada entidad existente en el código actual tiene un único módulo responsable de escribirla; los demás contextos solamente pueden solicitar operaciones o consultar representaciones que el propietario exponga.

| Módulo / contexto | Entidad o dato | Propietario / único escritor | Otros módulos que pueden necesitarlo | Regla |
|---|---|---|---|---|
| **Usuario** | `Usuario` | Usuario | Academic, AI, Reminders | Los demás contextos reciben identidad o solicitan información mediante contratos; no escriben `Usuario`. |
| **Usuario** | `TelegramLinkToken` / vínculo Telegram | Usuario | Reminders | Reminders consume la información necesaria para enviar notificaciones, pero no administra el vínculo. |
| **Academic** | `Task` | Academic | AI, Reminders | Academic es el único escritor de tareas académicas. AI y Reminders consumen operaciones o consultas controladas. |
| **AI** | `Conversation` | AI | Ninguno | La conversación pertenece al contexto de interacción inteligente. |
| **AI** | `Turn` / turnos de conversación | AI | Ninguno | AI administra el historial y estado conversacional. |
| **Reminders** | `Reminder` | Reminders | Academic, Usuario | Reminders es el único escritor de recordatorios. La referencia `task_id` no convierte a Academic en propietario del recordatorio. |
| **Reminders** | `Notification` | Reminders | Usuario, Telegram | Reminders registra y gestiona las notificaciones; Telegram es un canal externo. |
| **Reminders** | `ReminderSchedule` | Reminders | Ninguno | La programación de recordatorios pertenece al ciclo de vida de Reminders. |

## Estado de persistencia

Actualmente la persistencia de estas entidades se implementa mediante repositorios en memoria en los módulos correspondientes. La tabla expresa la **propiedad conceptual y modular del dato**, no presupone que exista todavía una tabla PostgreSQL implementada para cada entidad.

## Auditoría de propiedad y dependencias

La auditoría se realizó sobre el código vigente del backend, recorriendo la estructura de `backend/app/modules/` y buscando dependencias cruzadas y acceso a repositorios de otros contextos.

### Comprobaciones realizadas

- Se identificaron los cuatro módulos actuales: `academic`, `ai`, `reminders` y `usuario`.
- Se revisaron las entidades presentes en los contextos y sus repositorios/adaptadores.
- Se buscaron referencias cruzadas entre módulos, especialmente imports hacia APIs inbound y repositorios outbound de otro contexto.
- Se verificó que `Task` tiene como repositorio propietario a Academic y que los repositorios de Reminders gestionan `Reminder`, `Notification` y `ReminderSchedule`.
- No se identificó en el código actual un segundo módulo que escriba directamente las mismas entidades de dominio. Por tanto, **no se detecta una violación de doble escritura de una misma entidad** en el estado auditado.
- Sí se identificaron **violaciones de frontera modular**, donde un contexto accede directamente a adaptadores internos de otro contexto. Estas violaciones se detallan a continuación.
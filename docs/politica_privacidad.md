# Política de tratamiento de datos personales

**Versión:** `2026-11-v1` · **Vigente desde:** 2026-11-01

Esta es la política que el estudiante acepta al registrarse en TAIA (RF-USR-10). La versión
`2026-11-v1` es la cadena que la API guarda en `users.consent_policy_version` cuando se crea la
cuenta; si el texto cambia, cambia la versión y se pide una aceptación nueva.

## 1. Responsable del tratamiento

TAIA es un asistente académico desarrollado como proyecto del curso *Task Artificial Intelligence
Assistant* de la Universidad Industrial de Santander (UIS). El responsable del tratamiento es el
equipo del proyecto, a través de su repositorio:
<https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant>.

El canal habilitado para consultas, reclamos y solicitudes sobre datos personales son los *issues*
de ese repositorio. No se publica un correo de soporte porque el proyecto no tiene personal
dedicado a atención al público; el issue deja rastro y permite responder por escrito.

## 2. Marco legal

Se aplican la **Ley 1581 de 2012** (protección de datos personales) y su **Decreto 1377 de 2013**
(reglamentario), que exigen la autorización **previa, expresa e informada** del titular y regulan
las transferencias internacionales de datos.

## 3. Datos que se tratan

La lista es la de [modelo_amenazas.md §6](modelo_amenazas.md#6-privacidad). No se recogen datos
que no estén aquí.

| Dato | Dónde se guarda | Para qué | ¿Obligatorio? |
|---|---|---|---|
| Nombre completo | `users.full_name` | Identificar la cuenta | Sí: sin nombre no hay cuenta |
| Correo electrónico | `users.email` | Iniciar sesión y recuperar la contraseña | Sí: es el identificador de acceso |
| Contraseña (solo hash PBKDF2-SHA256) | `users.password_hash` | Autenticar | Sí: la contraseña en claro nunca se guarda |
| Identificador de Telegram | `users.telegram_user_id` | Vincular la cuenta y enviar recordatorios | No: solo si el estudiante vincula Telegram |
| Asignaturas, horario, tareas y exámenes | Módulo Academic | Organizar la vida académica y calcular recordatorios | Sí para usar el asistente académico |
| Planes de estudio y sesiones generadas | Módulo Academic | Sugerir cuándo estudiar | No: se generan cuando el estudiante los pide |
| Recordatorios y notificaciones | Módulo Reminders | Avisar de fechas y recordatorios | No: se crean con las tareas y el horario |
| Mensajes al agente | `conversation_messages`, 24 h | Interpretar la solicitud y responder | Sí para usar el chat |
| Token de dispositivo (FCM) | `sessions.fcm_token` | Notificaciones push (RF-NOT, pendiente) | No: solo si se activan las notificaciones |
| Correo de intentos fallidos | `failed_login_attempts`, 24 h | Frenar fuerza bruta (RNF-03) | Automático, por seguridad |
| `user_id` en los logs | stdout del contenedor | Operación y diagnóstico (RNF-05) | Automático |

**No se recogen:** teléfono (D-09), dirección, ubicación, documentos de identidad, datos de salud,
datos biométricos, datos de menores ni la dirección IP en los logs de la aplicación (RNF-05).

## 4. Finalidades del tratamiento

1. Crear y mantener la cuenta del estudiante y autenticarlo.
2. Prestar las funciones académicas: asignaturas, horario, tareas, exámenes, planes de estudio y
   recordatorios.
3. Interpretar los mensajes dirigidos al asistente y responderlos.
4. Enviar recordatorios y notificaciones que el estudiante haya configurado o aceptado.
5. Proteger el servicio: límites de uso, detección de fuerza bruta y alertas de seguridad.
6. Cumplir obligaciones legales y atender consultas, reclamos y solicitudes del titular.

No se usan los datos para publicidad, perfilamiento comercial ni venta a terceros.

## 5. Autorización

- La autorización se pide **en el registro**. El estudiante marca explícitamente que leyó y acepta
  esta política; no hay casilla premarcada ni aceptación implícita.
- **Sin aceptación la cuenta no se crea.** La API responde `422` y no escribe nada en la base.
- Al aceptar se guardan dos datos: la **fecha y hora** de la aceptación
  (`users.consent_accepted_at`) y la **versión** aceptada (`users.consent_policy_version`).
- La autorización cubre las finalidades de la sección 4 y las transferencias de la sección 6.

El detalle técnico del flujo —campos, respuestas y qué se guarda— está en
[flujo_consentimiento.md](flujo_consentimiento.md).

## 6. Transferencias y transmisiones internacionales

TAIA opera desde Colombia, pero se apoya en proveedores fuera del país. Al aceptar esta política,
el estudiante autoriza estas transferencias:

| Destino | Qué recibe | Para qué | País o región |
|---|---|---|---|
| Supabase (PostgreSQL) | Todos los datos de las tablas, cifrados en tránsito | Alojar la base de datos | `us-west-2` (Estados Unidos) |
| Google (Gemini) | Solo el texto del mensaje del estudiante y el contexto de la conversación; sin nombre, correo ni identificadores | Generar la respuesta del asistente | Estados Unidos |
| Groq | Lo mismo que Gemini, solo si se activa el respaldo de [ADR-0011](adr/0011-usar-groq-como-proveedor-llm-de-respaldo.md) | Respaldo del proveedor LLM | Estados Unidos |
| Telegram | Identificador de Telegram y el texto del recordatorio | Vincular la cuenta y enviar recordatorios | Internacional |
| Firebase (FCM) | Token de dispositivo y el texto de la notificación push, cuando exista RF-NOT | Entregar notificaciones push | Internacional |
| Dokploy | Logs de la aplicación, sin cuerpos, tokens ni contraseñas | Operar y diagnosticar el servicio | El del servidor contratado |

Los mensajes que recibe el proveedor LLM no incluyen identificadores del estudiante: el texto se
envía con el `user_id` solo del lado de TAIA.

## 7. Conservación

| Dato | Tiempo |
|---|---|
| Cuenta, nombre, correo, contraseña y datos académicos | Mientras la cuenta esté activa. Desactivarla no la borra (RT-04, RF-USR-09) |
| Mensajes al agente | 24 horas; después se borran físicamente |
| Intentos fallidos de inicio de sesión | 24 horas |
| Tokens de sesión, renovación y recuperación vencidos | Se revocan y se eliminan al vencer |
| Logs de la aplicación | Los del contenedor, según la retención de Dokploy |

## 8. Derechos del titular

El estudiante puede, en cualquier momento:

- **Conocer** qué datos suyos se tratan y para qué.
- **Actualizar y rectificar** su nombre y correo.
- **Suprimir** sus datos y **revocar** la autorización.
- **Solicitar prueba** de la autorización otorgada (la fecha y la versión quedan guardadas).
- **Presentar quejas** ante la Superintendencia de Industria y Comercio.

**Cómo ejercerlos.** Abriendo un *issue* en el repositorio del proyecto, indicando el correo de la
cuenta y el derecho que se quiere ejercer. Se responde por el mismo medio:

- **Consultas:** 10 días hábiles, prorrogables 5 más.
- **Reclamos:** 15 días hábiles, prorrogables 8 más.

**Revocar la autorización.** Como el tratamiento es indispensable para prestar el servicio, revocar
la autorización implica **desactivar la cuenta** (RF-USR-09): se revocan las sesiones, se
desvincula Telegram, se eliminan los tokens de dispositivo y se cancelan los recordatorios. Los
datos no se borran físicamente, porque las tareas y asignaturas sostienen registros académicos
(RT-04); quedan inaccesibles y sin tratamiento posterior.

## 9. Seguridad

- La contraseña se guarda solo como hash PBKDF2-SHA256 con sal e iteraciones (RNF-01, T-13).
- El tráfico va por TLS; el HTTP responde `301` a HTTPS (RNF-04, T-17).
- Los tokens de acceso son JWT de 30 minutos, ligados a una sesión revocable (T-08).
- Los logs no guardan cuerpos, contraseñas, tokens ni la IP de origen (RNF-05).
- El acceso a la base y a los secretos está restringido al entorno de despliegue (RNF-02).

## 10. Menores de edad

El servicio está dirigido a estudiantes universitarios mayores de edad. No se recogen datos de
niños, niñas o adolescentes. Si se detecta una cuenta de un menor sin la autorización de su
representante legal, se desactiva hasta que esa autorización exista (Ley 1581 de 2012, art. 7).

## 11. Cambios a esta política

Cualquier cambio sustancial se publica como una **versión nueva** (por ejemplo `2026-11-v2`) y se
pide una aceptación nueva antes de seguir usando el servicio. La versión aceptada por cada cuenta
queda registrada, así que siempre se puede saber qué texto aceptó cada estudiante y cuándo.

## 12. Relación con los requerimientos

| Requerimiento | Cómo se cumple |
|---|---|
| RF-USR-10 | Esta política, la aceptación obligatoria en el registro y las dos columnas de constancia |
| RF-USR-09 | Desactivación como forma de revocar la autorización sin borrar los registros académicos |
| RNF-05 | Sin teléfono, sin IP en logs y con retención de 24 horas para mensajes e intentos fallidos |
| RNF-01, RNF-04 | Hash de contraseña y TLS |

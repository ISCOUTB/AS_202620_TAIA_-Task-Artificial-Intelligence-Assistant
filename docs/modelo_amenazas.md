# Modelo de amenazas y plan de mitigación (S13)

Estado revisado: `main`, del commit `2c69809` al cierre del 2026-10-30. La arquitectura de
seguridad resultante está en [arc42 §8.12](arc42/08-conceptos-transversales.md#812-arquitectura-de-seguridad)
y las amenazas aceptadas en [arc42 §11.13](arc42/11-riesgos-y-deudas-tecnicas.md#1113-amenazas-aceptadas).

## 1. Método

- **Modelo:** STRIDE sobre los elementos de nuestro C4: [C4-C2](c4/C4-C2.md) (Estudiante, App
  Móvil, API TAIA, Base de Datos, Telegram, Proveedor LLM) y [C4-C3](c4/C4-C3.md) (módulos
  Usuario, Academic, AI y Reminders).
- **Referencias:** cada amenaza cita su categoría de [OWASP Top 10:2025](https://top10.owasp.org/2025/)
  (A01 a A10) o de OWASP Top 10 for LLM Applications 2025 (LLM01 a LLM10).
- **Priorización:** probabilidad (P) e impacto (I) en escala 1 (baja) a 3 (alta).
  Prioridad = P × I: 9 crítica, 6 alta, 3 o 4 media, 1 o 2 baja.
- **Dueños:** luis20072002 aplicó las mitigaciones de esta semana; las demás se reparten entre
  val, dei0811 y mark.

## 2. Amenazas priorizadas

| ID | Elemento C4 | STRIDE | OWASP | Amenaza | P | I | Prio. |
|---|---|---|---|---|---|---|---|
| T-06 | AI → Proveedor LLM | DoS | LLM10 | Un usuario agota la cuota del LLM con mensajes en serie | 3 | 3 | 9 |
| T-07 | Usuario (`/users/login`) | Spoofing | A07 | Fuerza bruta de contraseñas | 3 | 3 | 9 |
| T-10 | Telegram → Usuario | Spoofing | A07 | Vincular un `telegram_user_id` ajeno sin pasar por el bot | 3 | 3 | 9 |
| T-01 | AI → Proveedor LLM | Tampering | LLM01, A05 | Inyección de prompt para cambiar la intención o las reglas | 3 | 2 | 6 |
| T-02 | AI → Proveedor LLM | Info. disclosure | LLM02 | Los mensajes del estudiante salen a un tercero | 3 | 2 | 6 |
| T-04 | AI → Academic | Elevation | LLM06 | El agente escribe o borra sin que el estudiante lo pida | 2 | 3 | 6 |
| T-09 | Academic, Reminders | Elevation | A01 | Acceder a datos de otro estudiante por su id (IDOR) | 2 | 3 | 6 |
| T-12 | API TAIA (imagen) | Tampering | A03, LLM03 | Dependencia con una vulnerabilidad conocida o adulterada | 2 | 3 | 6 |
| T-15 | Proveedor LLM | DoS | A10 | Caída o saturación del proveedor | 3 | 2 | 6 |
| T-17 | App Móvil → API TAIA | Info. disclosure | A04 | Interceptar el JWT o los datos en tránsito | 2 | 3 | 6 |
| T-08 | Usuario (sesiones) | Spoofing | A07 | Un JWT robado sigue válido y no se puede revocar | 2 | 2 | 4 |
| T-14 | API TAIA (logs) | Repudiation | A09 | Ataques sin registro ni alerta | 2 | 2 | 4 |
| T-16 | App Móvil | Info. disclosure | A02 | Respaldo de datos de la app y tráfico en claro en Android | 2 | 2 | 4 |
| T-11 | API TAIA (`/metrics`, `/docs`) | Info. disclosure | A02 | Reconocimiento de rutas y tráfico sin sesión | 3 | 1 | 3 |
| T-13 | Base de Datos (`users`) | Info. disclosure | A04 | Contraseñas legibles si se filtra la base | 1 | 3 | 3 |
| T-03 | AI (contexto) | Tampering | LLM04 | Envenenamiento del contexto conversacional | 1 | 2 | 2 |
| T-05 | AI → Proveedor LLM | Info. disclosure | LLM07 | Fuga del prompt de sistema | 2 | 1 | 2 |

## 3. Plan de mitigación

| ID | Mitigación | Dueño | Estado | Evidencia |
|---|---|---|---|---|
| T-06 | 30 mensajes por hora y 200 por día; `429` sin llamar al LLM (RF-AGT-19) | luis20072002 | Hecha | `1a3696a`, [prueba](../backend/tests/test_ai_usage_limit.py) |
| T-07 | 5 fallos por correo cada 15 min; `429` (RNF-03) | luis20072002 | Hecha | `14c487e`, [prueba](../backend/tests/test_usuario_login_rate_limit.py) |
| T-10 | Webhook con `X-Telegram-Bot-Api-Secret-Token`; el id sale del update (RF-TEL-02) | luis20072002 | Hecha | `2c69809`, [prueba](../backend/tests/test_usuario_telegram_link.py) |
| T-01 | Reglas en `systemInstruction`, mensaje aparte y delimitado, marcas neutralizadas (RF-AGT-18) | luis20072002 | Hecha | `dbe5634`, [prueba](../backend/tests/test_ai_prompt_injection.py) |
| T-02 | El LLM solo recibe el texto, sin identificadores; falta la autorización del titular (RF-USR-10) | val | Pendiente | [§6](#6-privacidad) |
| T-04 | Lista cerrada de intenciones y confirmación antes de escribir (ADR-0005, RF-AGT-04) | mark | Hecha | [prueba](../backend/tests/test_ai_create_task_confirmation.py) |
| T-09 | El usuario sale del token y lo ajeno responde `404` (RT-02) | dei0811 | Hecha | [prueba](../backend/tests/test_academic_subjects_api.py) |
| T-12 | Locks con hash, pip-audit en CI y PyJWT/certifi actualizados | luis20072002 | Hecha | `41aa1d2`, [§5](#5-análisis-de-dependencias) |
| T-15 | Respaldo Groq tras Gemini ([ADR-0011](adr/0011-usar-groq-como-proveedor-llm-de-respaldo.md)); si fallan todos, falla cerrado (ADR-0007) | luis20072002 | Hecha; se activa con `GROQ_API_KEY_1` | [prueba](../backend/tests/test_ai_fallback_llm.py), [§4](#4-riesgos-del-componente-generativo) |
| T-17 | TLS en Traefik; HTTP responde 301 a HTTPS (RNF-04) | mark | Hecha | `curl` del 2026-10-30: 200 y 301 |
| T-08 | Expiración del JWT a 30 min; falta renovación y revocación (RF-USR-03, 04) | val | Pendiente | [estado_backend.md](estado_backend.md) |
| T-14 | Logs JSON sin datos sensibles (RNF-05); faltan alertas | val | Pendiente | [observability.py](../backend/app/shared/adapters/inbound/observability.py) |
| T-16 | `allowBackup` y `usesCleartextTraffic` en `false`, R8 en release | luis20072002 | Hecha | `1cf3d03` |
| T-11 | `/metrics` exige JWT (RT-01); `/docs` se acepta como riesgo | luis20072002 | Hecha | `15ecb9b`, [§11.13](arc42/11-riesgos-y-deudas-tecnicas.md#1113-amenazas-aceptadas) |
| T-13 | PBKDF2-SHA256 con 310 000 iteraciones y sal (RNF-01) | dei0811 | Hecha | [hasher](../backend/app/modules/usuario/adapters/outbound/pbkdf2_password_hasher.py) |
| T-03 | Riesgo aceptado: el LLM no recibe el historial | mark | Aceptada | [§11.13](arc42/11-riesgos-y-deudas-tecnicas.md#1113-amenazas-aceptadas) |
| T-05 | Riesgo aceptado: el prompt no tiene secretos y ya es público | mark | Aceptada | [§11.13](arc42/11-riesgos-y-deudas-tecnicas.md#1113-amenazas-aceptadas) |

**Correspondencia con la prioridad.** Las tres amenazas críticas (T-06, T-07, T-10) se mitigaron
primero, en la semana del modelado. De las siete altas, seis están hechas; T-02 queda pendiente
con su requerimiento (RF-USR-10) asignado. T-11, de prioridad media, se
atendió en la misma semana porque costaba una línea de código.

## 4. Riesgos del componente generativo

| Riesgo | Cómo se materializa en TAIA | Mitigación |
|---|---|---|
| Inyección de prompt (LLM01) | El estudiante escribe "ignora tus instrucciones..." en `/ai/message` | T-01. Además, aunque el modelo obedezca, el usuario sale del token y solo se ejecutan operaciones de una lista cerrada: la prueba de aceptación lo comprueba con un modelo que obedece |
| Fuga de datos (LLM02, LLM07) | El modelo revela datos de otro estudiante o su prompt | El LLM nunca recibe datos de otros usuarios ni identificadores (RF-AGT-17); el prompt no contiene secretos (T-05) |
| Envenenamiento del contexto (LLM04) | Un mensaje anterior condiciona interpretaciones futuras | El historial se guarda, pero no se envía al LLM; la acción pendiente expira a los 10 min y exige confirmación (T-03) |
| Salida insegura (LLM05) | El modelo devuelve campos o intenciones inventados | JSON con esquema fijo; los campos desconocidos se descartan y una intención no reconocida es `unknown` (`gemini_llm.py`, `_to_interpretation`) |
| Agencia excesiva (LLM06) | El modelo ejecuta acciones no pedidas | T-04 |
| Consumo sin límite (LLM10) | Mensajes en serie agotan la cuota | T-06 |

**Evaluación del respaldo** (`tools/eval_llm.py`, 100 mensajes, 2026-10-30):

| Proveedor y reglas | Intención | Campos | Fechas mal | p95 |
|---|---|---|---|---|
| Gemini flash-lite, reglas anteriores ([resultado](evaluacion_ia/resultado_s1_100.json)) | 0,889 | 101/110 | 0 | 2 191 ms |
| Groq gpt-oss-120b, reglas anteriores ([resultado](evaluacion_ia/resultado_groq_s1_100.json)) | 0,899 | 82/110 | 18 | 1 111 ms |
| Groq, con el día de la semana ([resultado](evaluacion_ia/resultado_groq_s1_100_con_dia.json)) | 0,919 | 98/110 | 1 | 1 199 ms |
| Gemini flash-lite, con el día de la semana ([resultado](evaluacion_ia/resultado_gemini_s1_100_con_dia.json)) | 0,929 | 105/110 | 0 | 1 690 ms |

Sin el día de la semana, Groq resolvía mal "el lunes" o "el domingo". Agregarlo a las reglas
compartidas corrigió las fechas en los dos proveedores. Groq queda a un campo del umbral de 0,9;
como solo responde cuando Gemini falla y toda escritura pide confirmación, activarlo lo decide el
equipo al configurar `GROQ_API_KEY_1`.

No aplican LLM08 (no hay embeddings ni RAG) ni LLM09 en escrituras, porque toda escritura se
confirma. LLM09 en las respuestas de ayuda se acepta en §11.13.

## 5. Análisis de dependencias

**Herramienta:** pip-audit 2.10.1, que consulta las bases de PyPI y OSV. Corre en cada push como
el paso `Audit dependencies for known vulnerabilities` de [ci.yml](../.github/workflows/ci.yml)
sobre los dos locks. Si encuentra una CVE, el job falla y CD no despliega.

**Hallazgos de la primera ejecución** (local, 2026-10-30, sobre `2c69809`):

| Paquete | Versión | Avisos | Qué se hizo |
|---|---|---|---|
| `pyjwt` | 2.10.1 | 22, entre ellos CVE-2026-32597 (`crit` sin validar) y CVE-2026-48523 (bypass de la lista de algoritmos con claves PyJWK) | Actualizado a 2.15.1. TAIA fija HS256 y no usa JWKS, así que la mayoría no era explotable, pero la librería firma todas las sesiones |
| `certifi` | 2026.7.22 | 2, GHSA-6q48-6c7w-9gw2 (raíz emSign retirada) | Actualizado a 2026.10.18 |
| `pyjwt` | 2.10.1 | PYSEC-2025-183, disputado por el proveedor y sin versión corregida | No aparece en 2.15.1; no hizo falta ignorarlo |

Después del cambio, pip-audit da "No known vulnerabilities found" en los dos locks. En el
pipeline, el paso pasó en el [run 41158064339](https://github.com/ISCOUTB/AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant/actions/runs/41158064339)
(commit `dbe5634`).

**SonarCloud** ([análisis público](https://sonarcloud.io/project/overview?id=ISCOUTB_AS_202620_TAIA_-Task-Artificial-Intelligence-Assistant))
tenía el Quality Gate en `ERROR` con tres vulnerabilidades del cliente Android (`kotlin:S7204`,
`xml:S5332`, `xml:S6358`) y un bug (`Web:S5254`). El CI no corría con cambios en `frontend/**`, así
que nadie lo vio hasta que falló el CI de `2c69809`. El CI ahora también corre con `frontend/**`.
`1cf3d03` cerró `xml:S5332`, `xml:S6358` y el bug; en el run 41158064339 el gate siguió en
`ERROR` solo por `kotlin:S7204`, que se atendió declarando `proguardFiles` en la versión release.
Los code smells nuevos no afectan al gate (mantenibilidad A).

**Límite:** el cliente Flutter solo depende de `cupertino_icons` y pip-audit no cubre paquetes de
Dart. Se revisará cuando la app agregue dependencias.

## 6. Privacidad

| Dato personal | Dónde | Finalidad | Sale hacia |
|---|---|---|---|
| Nombre completo y correo | `users` | Identificar la cuenta e iniciar sesión | Supabase (base de datos) |
| Hash de contraseña | `users` | Autenticar | No sale |
| `telegram_user_id` | `users` | Vincular la cuenta y enviar recordatorios | Telegram |
| `fcm_token` | `sessions` | Notificaciones push (RF-NOT, pendiente) | Firebase, cuando exista |
| Tareas, asignaturas, horario y período | Módulo Academic | Organizar la vida académica | Supabase; título de la tarea a Telegram en un recordatorio |
| Mensajes al agente | `conversation_messages`, 24 h | Interpretar la solicitud | Proveedor LLM: solo el texto, sin identificadores |
| Correo de intentos fallidos | `failed_login_attempts`, 24 h | Seguridad (RNF-03) | No sale |
| `user_id` en los logs | stdout del contenedor | Operación (RNF-05) | Dokploy |

**Base del tratamiento.** La Ley 1581 de 2012 y su decreto reglamentario 1377 de 2013 exigen la
autorización previa, expresa e informada del titular. La transferencia a servicios fuera de
Colombia (Supabase en `us-west-2`, Google, Telegram y, según ADR-0011, Groq) también requiere esa
autorización. **Hoy TAIA no la recoge**: el registro no pide consentimiento. Se agregó
**RF-USR-10** a los requerimientos (pendiente, dueña val).

**Minimización ya aplicada:** no se pide teléfono (D-09); el LLM no recibe identificadores; los
mensajes y los intentos fallidos se borran a las 24 horas; los logs no guardan cuerpos ni tokens.

## 7. Secretos

Barrido del contrato §9 sobre `2c69809`: **ninguna credencial**. `git grep` solo encuentra nombres
de variables. `git log -S'BEGIN PRIVATE KEY'` encuentra `a3f4d82` y `-S'AIza'` encuentra
`c57f10b`, pero ambos son texto de documentación que cita el patrón, no una clave. No hay `.env`
versionado. Los secretos viven en el Environment de Dokploy (RNF-02).

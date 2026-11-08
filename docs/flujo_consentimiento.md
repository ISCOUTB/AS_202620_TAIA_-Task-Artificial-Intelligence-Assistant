# Registro del consentimiento

Cómo se obtiene, se valida y se guarda la autorización de tratamiento de datos (RF-USR-10) que
exige la [política de privacidad](politica_privacidad.md). Este documento describe el flujo
acordado; el código y el contrato se actualizan en los commits siguientes.

## 1. Dónde se pide

En el **registro** (`POST /users`). No hay otro punto de entrada: una cuenta solo puede nacer con
la autorización aceptada.

Todavía **no existe pantalla de registro** en `frontend/`: la app solo tiene splash y bienvenida.
Cuando se construya, la casilla de aceptación debe llegar **desmarcada** y el botón de crear cuenta
debe estar bloqueado hasta marcarla. Este documento fija el contrato para que la pantalla no tenga
que decidir nada por su cuenta.

## 2. Cuerpo de la petición

```json
{
  "full_name": "Ana Pérez",
  "email": "ana@example.com",
  "password": "una contraseña larga",
  "consent_accepted": true,
  "consent_policy_version": "2026-11-v1"
}
```

| Campo | Tipo | Regla |
|---|---|---|
| `consent_accepted` | boolean | Obligatorio. Tiene que ser `true` |
| `consent_policy_version` | string | Obligatorio. Debe ser exactamente la versión vigente (`2026-11-v1`) |

La versión se envía desde el cliente para que quede constancia de **qué texto** vio el estudiante.
Si el cliente manda una versión vieja, el registro falla y debe volver a mostrar la política: es
mejor rechazar que guardar una aceptación de un texto que ya cambió.

## 3. Respuestas

| Caso | Estado | Efecto |
|---|---|---|
| Acepta y la versión coincide | `201` | Se crea la cuenta con fecha y versión |
| `consent_accepted` es `false` | `422` | No se crea nada |
| Falta `consent_accepted` | `422` | No se crea nada |
| Falta `consent_policy_version` | `422` | No se crea nada |
| Versión distinta de la vigente | `422` | No se crea nada; el cliente recarga la política |
| Correo ya registrado | `409` | Igual que hoy (RF-USR-01) |

El `422` es el mismo código que ya usa la API para datos inválidos, así que el cliente no necesita
un caso especial.

## 4. Qué se guarda

En la misma transacción que crea la fila de `users`:

| Columna | Valor |
|---|---|
| `consent_accepted_at` | Instante de la aceptación, en UTC (`now_bogota()` convertido) |
| `consent_policy_version` | La versión aceptada, por ejemplo `2026-11-v1` |

La definición de las columnas está en [diccionario_datos.md §5.1](diccionario_datos.md#51-users).
La restricción `CHECK ((consent_accepted_at IS NULL) = (consent_policy_version IS NULL))` impide
que una fila quede con media constancia.

La respuesta `201` incluye `consent_accepted_at` y `consent_policy_version` para que el cliente
pueda mostrar la constancia sin una petición extra.

## 5. Cuentas anteriores

Las cuentas creadas antes de esta entrega tienen ambas columnas en `NULL`. No se les inventa una
aceptación: la política no existía cuando se registraron.

Esta entrega **no las bloquea**. Si el equipo decide exigirles la aceptación, el camino es una
pantalla de aceptación posterior, no un `422` silencioso en el login; queda fuera del alcance de
RF-USR-10.

## 6. Cambios de versión

- La versión vigente vive en una sola constante del backend (`CURRENT_POLICY_VERSION`).
- Cambiar el texto de la política obliga a cambiar esa constante y la fecha de vigencia del
  documento.
- Un estudiante que aceptó `2026-11-v1` conserva esa constancia. Pedirle una aceptación nueva es
  trabajo de una pantalla futura; la base ya distingue quién aceptó qué versión.

**Limitación conocida:** se guarda la **última** aceptación, no un historial. Si más adelante se
pide aceptar una versión nueva, la anterior se sobrescribe. Para conservar el historial completo
haría falta una tabla `user_consents`; no se incluye en esta entrega porque RF-USR-10 solo pide
fecha y versión, y el volumen actual no lo justifica.

## 7. Relación con el modelo de amenazas

- **T-02** (repudio sobre el tratamiento de datos) se cierra con esta constancia: queda registrado
  que el estudiante aceptó, cuándo y qué versión.
- **RNF-05**: la aceptación no se registra en los logs; solo la columna. Los logs siguen sin
  cuerpos ni identificadores de más.

## 8. Cómo se verifica

| Prueba | Qué comprueba |
|---|---|
| Registro sin los campos | `422` y la tabla `users` no crece |
| `consent_accepted: false` | `422` |
| Versión distinta | `422` |
| Registro válido | `201`, con fecha y versión en la respuesta y en la fila |
| Cuenta anterior sin consentimiento | el inicio de sesión sigue funcionando aunque sus columnas estén en `NULL` |

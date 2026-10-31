# Verificación de dependencias del cliente Flutter

`pip-audit` solo cubre Python. El cliente Flutter fija sus dependencias en
`frontend/pubspec.lock`, así que ese lock se verifica con una herramienta propia.
Todo lo afirmado aquí se reproduce con un comando.

## Cómo se ejecuta

```bash
python tools/verificar_dependencias_dart.py            # sin red
python tools/verificar_dependencias_dart.py --online   # consulta OSV
python tools/verificar_dependencias_dart.py --json docs/verificacion_dependencias_dart.json
```

No hace falta tener Flutter instalado: el verificador lee los dos archivos y, si
se pide, consulta la API pública de OSV.

## Qué comprueba

| Regla | Por qué |
| --- | --- |
| Cada paquete tiene `version` | Una versión vacía deja la instalación a merced de la resolución del momento. |
| Cada paquete alojado tiene `sha256` | Es el hash que `pub get` contrasta; sin él no hay garantía de integridad. |
| El origen alojado es `https://pub.dev` | Un origen distinto sería un paquete suplantado. |
| No hay dependencias `git` ni `path` | Traerían código que nadie revisó ni versionó con hash. |
| Cada directa de `pubspec.yaml` está en el lock con su tipo | Detecta un lock viejo o editado a mano. |
| Con `--online`, OSV no reporta avisos del ecosistema `Pub` | Cubre CVE que pip-audit no ve. |

## Resultado actual

| Métrica | Valor |
| --- | --- |
| Paquetes en `pubspec.lock` | 27 |
| Alojados en pub.dev | 24 |
| Del SDK (`flutter`) | 3 |
| Directas (`cupertino_icons`, `flutter_lints`) | 2 |
| Sin versión / sin `sha256` / origen no permitido | 0 / 0 / 0 |
| Avisos de OSV | 0 |

Salida completa: [`verificacion_dependencias_dart.json`](verificacion_dependencias_dart.json).
Veredicto de la herramienta: **ok**.

## Límites

- Se verifica que la restricción de `pubspec.yaml` exista y que el tipo del lock
  coincida; que la versión resuelta la satisfaga lo garantiza `pub get`.
- `--online` depende de la red y de la disponibilidad de OSV. En el CI corre en
  el mismo paso que pip-audit, así que una caída de OSV detiene el despliegue en
  lugar de dejar pasar una dependencia vulnerable.
- Los paquetes del SDK de Flutter no se consultan: su versión la fija el SDK.

## Cuándo se actualiza

- Al cambiar `pubspec.yaml` o `pubspec.lock`, el CI ejecuta el verificador y
  falla si el lock queda inconsistente.
- Al agregar una dependencia directa, se regenera el JSON con
  `--json docs/verificacion_dependencias_dart.json` y se revisan los avisos de
  OSV antes de mezclar el cambio.

# Contrato de API — S7

El contrato versionado de la API principal de TAIA está en [`openapi.json`](openapi.json).

- **Especificación:** OpenAPI 3.1.
- **Versión de API:** `1.0.0`.
- **Transporte:** HTTP síncrono.
- **Formato de intercambio:** JSON.
- **Prueba de contrato:** `backend/tests/test_api_contract.py`.
- **Cliente generado:** `backend/generated/taia_api_client.py`.
- **Generador:** `python tools/generate_api_client.py`.
- **Pipeline:** `.github/workflows/ci.yml`.

## Verificación local

```bash
python -m pytest backend/tests/test_api_contract.py -q
python tools/generate_api_client.py
git diff --exit-code -- backend/generated/taia_api_client.py
```

La prueba `test_incompatible_change_is_detected` modifica en memoria la superficie implementada y verifica que el comparador del contrato lance `AssertionError`. Esto demuestra que una modificación incompatible es detectable sin dejar el pipeline normal en rojo.

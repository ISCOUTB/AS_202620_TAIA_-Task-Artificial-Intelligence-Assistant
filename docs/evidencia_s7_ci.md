# Evidencia S7 — CI y trazabilidad

## Qué queda comprobado en el repositorio

1. `.github/workflows/ci.yml` ejecuta `backend/tests/test_api_contract.py`.
2. El mismo workflow regenera `backend/generated/taia_api_client.py`.
3. El workflow falla si la regeneración produce diferencias (`git diff --exit-code`).
4. `docs/evidencia_s7_contract_failure.txt` conserva una ejecución reproducible del cambio incompatible.
5. `git log --follow -- docs/api/openapi.json` debe utilizarse en la revisión de Git para evidenciar la evolución del contrato.

## Evidencia que debe agregarse después del push

- SHA del commit revisado.
- Nombre/número del run de GitHub Actions.
- URL pública del run.
- Resultado `success`.
- Paso `Run API contract test` en verde.
- Paso `Regenerate API client from OpenAPI contract` en verde.
- Paso `Verify generated client is synchronized` en verde.

No se registra una URL ficticia: estos datos solo pueden provenir de una ejecución real de GitHub Actions.

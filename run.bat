@echo off
rem Arranque local de TAIA.
rem
rem Este script NO fija ninguna credencial. Antes definía dos valores por defecto:
rem   DATABASE_URL=<configuracion-local-en-backend.env>
rem   un secreto JWT de desarrollo
rem El segundo contradecía RNF-02, que exige que sin secreto la API no arranque,
rem y era además un secreto publicado en el repositorio. El primero era peor:
rem load_dotenv() no sobrescribe variables ya definidas, así que ese valor tenía
rem prioridad sobre backend/.env y el archivo del desarrollador se ignoraba en
rem silencio.
rem
rem La configuración llega de backend/.env (ignorado por git). Copie la
rem plantilla la primera vez:
rem   copy .env.example backend\.env

if not exist "backend\.env" (
  echo [TAIA] Falta backend\.env. Copie la plantilla y ajuste los valores:
  echo        copy .env.example backend\.env
  exit /b 1
)

rem La clave de Gemini es obligatoria: la composicion ocurre en app/main.py y el
rem proceso no arranca sin ella. `for /f` separa el valor tras el "="; si la
rem linea es "GEMINI_API_KEY=" el valor llega vacio y la variable no queda
rem definida.
rem
rem No se usa findstr /B a proposito: /B exige que el texto empiece en la
rem posicion 0 y un .env guardado como UTF-8 con BOM (habitual en Windows, y es
rem lo que produce `Set-Content -Encoding utf8` de PowerShell 5.1) empieza con
rem EF BB BF, con lo que /B no encuentra nada y el arranque se rechaza siempre.
rem Sin /B el busqueda tambien encuentra una linea comentada; en ese caso la
rem comprobacion pasa y la propia API falla al arrancar con su RuntimeError,
rem que es un fallo igualmente explicito.
setlocal
set "_GEMINI_API_KEY="
for /f "tokens=1,* delims==" %%A in ('findstr /C:"GEMINI_API_KEY=" "backend\.env"') do set "_GEMINI_API_KEY=%%B"
if not defined _GEMINI_API_KEY (
  echo [TAIA] GEMINI_API_KEY vacio en backend\.env. Defina la clave en
  echo        https://aistudio.google.com/apikey
  endlocal & exit /b 1
)
endlocal

python -m alembic -c backend/alembic.ini upgrade head || exit /b 1
python -m uvicorn app.main:app --app-dir backend --reload
Perfecto — vamos paso a paso. Ejecuta los comandos tal cual y dime dónde te quedas o si algún paso falla.

Abrir terminal y moverte a la carpeta backend:
En PowerShell (recomendado):
cd 'c:\Users\aflamerich\Documents\Curso\AI4Devs\proyecto-final\backend'
En CMD:
cd c:\Users\aflamerich\Documents\Curso\AI4Devs\proyecto-final\backend
Crear y activar un entorno virtual (Windows):
PowerShell:
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
CMD:
python -m venv .venv
.venv\Scripts\activate.bat
(Verás el prompt cambiar a (.venv))

Instalar dependencias mínimas:
PowerShell / CMD:
pip install fastapi "uvicorn[standard]" PyJWT python-dotenv
Arrancar la API (en la misma carpeta backend):
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
Deja esta terminal corriendo (verás logs). Si hay errores, pégamelos.

Obtener token JWT (nueva terminal):
Usando curl (Git Bash / WSL / Linux):
curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login\" -H "Content-Type: application/json" -d '{"username":"admin","password":"Admin2026"}'

PowerShell:
$body = '{"username":"admin","password":"Admin2026"}'; Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/auth/login -Method Post -Body $body -ContentType 'application/json'

La respuesta contendrá access_token. Cópialo.

Ejecutar los pollers (tercer terminal; en la misma carpeta backend):
Modo mock (no necesitas servidor modbus):
set HW_MODE=mock
python -m app.modules.sw.run_polling_example
Modo tcp (si tienes servidor modbus en tu PC):
set HW_MODE=tcp
set MODBUS_HOST=127.0.0.1
set MODBUS_PORT=502
python -m app.modules.sw.run_polling_example
(En PowerShell usa $env:HW_MODE='mock' y luego python -m ...)

Consultar el endpoint de estado (usa el token obtenido). Ejemplo con curl:
curl -s -H "Authorization: Bearer <TU_TOKEN_AQUI>" http://127.0.0.1:8000/api/v1/modbus/status | jq

O en PowerShell:

$hdr = @{ Authorization = "Bearer <TU_TOKEN_AQUI>" }; Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/modbus/status -Headers $hdr

Respuesta esperada: un JSON con entries por poller id. Cada entrada incluirá:

last_request (function/address/count/unit_id)
last_value
last_error (si hubo)
last_updated (timestamp)
raw_request_hex: agrupado como "0xAA 0xBB ..."
raw_response_hex: agrupado como "0xAA 0xBB ..."
Parar:
Para detener pollers: Ctrl+C en la terminal donde corren.
Para detener el servidor uvicorn: Ctrl+C en la terminal del servidor.
Desactivar entorno virtual:
deactivate
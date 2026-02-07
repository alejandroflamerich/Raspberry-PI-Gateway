Actúa como un senior full-stack engineer. Necesito implementar una consola web (command console) persistente en mi app.

OBJETIVO

1. Frontend: crear un componente de consola llamado "Console" que esté presente en todas las páginas (layout global).
2. Backend: crear un módulo CLI en backend/app/modules/sw/cli que exponga endpoints para:
    - listar comandos disponibles
    - ejecutar un comando con argumentos
    - devolver salida estructurada + logs + errores
    - (opcional) streaming simple por polling (no websockets por ahora)

RESTRICCIONES IMPORTANTES DE SEGURIDAD

- NO ejecutar comandos del sistema operativo (NO shell, NO subprocess arbitrario).
- Los comandos deben ser “registrados” en un registry (whitelist).
- Validar entrada: nombre de comando + args tipados.
- Requerir autenticación (si ya existe JWT, usarlo). Si no existe, dejar hooks claros para integrarlo.
- Limitar salida y tiempo de ejecución (timeout y max chars).

FRONTEND REQUERIMIENTOS (React + Vite)
Ubicación: frontend/src/components/console
Crear:

- frontend/src/components/console/Console.tsx
- frontend/src/components/console/console.css (o usar tailwind si ya existe)
- frontend/src/components/console/index.ts

UX/FEATURES:

- Consola tipo overlay docked abajo (como devtools), colapsable.
- Debe verse en todas las páginas: integrar en App layout (ej: App.tsx o Layout.tsx).
- Input de comando con placeholder ("help" / "commands").
- Historial (arriba) con:
    - timestamp
    - comando ejecutado
    - status (ok/error)
    - salida (texto) y/o JSON pretty
- Soporte para atajos:
    - tecla ` (backtick) abre/cierra
    - Esc cierra
    - ↑/↓ navega historial de comandos
- Botones: Clear, Help/Commands.
- Tema: oscuro, minimal, profesional.

API Frontend:

- GET /api/cli/commands -> lista de comandos disponibles (name, description, args schema)
- POST /api/cli/execute -> { command: string, args: object } -> { ok, output, data?, logs?, error? }

Manejo de errores:

- Mostrar errores del backend en rojo.
- Si el backend responde 401, mostrar “Not authenticated”.

BACKEND REQUERIMIENTOS (FastAPI)
Ubicación: backend/app/modules/sw/cli
Crear estructura:
backend/app/modules/sw/cli/
**init**.py
router.py
models.py
registry.py
commands/
**init**.py
health.py
echo.py

Implementación:

1. models.py: Pydantic models

- CommandInfo (name, description, args_schema)
- ExecuteRequest (command, args)
- ExecuteResponse (ok, output, data, logs, error)

2. registry.py:

- Un registry central con:
    - register_command(name, handler, description, args_schema)
    - list_commands()
    - execute(command, args) con validación
- Timeout (ej. 3-5s) y max_output_chars

3. commands/:

- echo: retorna el texto que se envía
- health: devuelve estado del backend (uptime, version, time)

4. router.py:

- APIRouter prefix="/api/cli"
- GET "/commands"
- POST "/execute"
- Integrar auth dependency si existe (placeholder si no)

5. Integración en FastAPI principal:

- Asegurar que el router se incluya en la app (ej: app.include_router(cli_router))

CALIDAD / ESTÁNDARES

- Código limpio, comentarios mínimos útiles.
- Tipado estricto en TS.
- Manejo de CORS si el front corre en otro puerto (dev).
- Respuestas consistentes y fáciles de renderizar.
- Añadir tests mínimos:
    - Backend: pytest para registry.execute + router endpoints (happy path + unknown command)
    - Frontend: al menos tests unitarios simples (si ya hay vitest) o dejar scaffolding.

ENTREGABLES

- Código completo de los archivos listados.
- Indicar exactamente qué líneas tocar en App.tsx/Layout.tsx para montar la consola global.
- Ejemplos de comandos a ejecutar desde la UI: "echo", "health", "commands".

IMPORTANTE
Si faltan piezas del proyecto (estructura real del backend o auth existente), asumir defaults razonables y dejar TODOs claros, sin bloquear la compilación.

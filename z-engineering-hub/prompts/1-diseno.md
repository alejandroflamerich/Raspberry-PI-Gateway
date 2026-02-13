Actúa como arquitecto senior full-stack (Python/FastAPI + React/Vite) para un proyecto “edge” orientado a Raspberry Pi (control de hardware + protocolos TCP tipo Modbus/DNP3 + envío a nube con TLS/JWT).

OBJETIVO
1) Crear una arquitectura simple, intuitiva y escalable.
2) Separar el repo en 2 carpetas principales: /backend y /frontend.
3) Permitir desarrollo en PC con simuladores/mocks y despliegue en Raspberry Pi sin cambiar código.
4) Incluir buenas prácticas: tipado, lint, tests, configuración por entornos, logging, estructura limpia, README.

RESTRICCIONES
- Backend: Python 3.11+ con FastAPI
- Frontend: React + Vite (TypeScript preferido)
- Mantener nombres claros, sin sobre-ingeniería.
- Pensar en “drivers hardware” aislados detrás de interfaces y con implementación mock.

ENTREGABLES
A) Propón la ARQUITECTURA (explicación corta + árbol de directorios).
B) Genera los ARCHIVOS iniciales mínimos (con contenido) para que el proyecto arranque.
C) Incluye scripts de ejecución local y pruebas.

--------------------------------------------
A) ESTRUCTURA DEL REPO (CREAR CARPETAS)
Quiero esta estructura base (puedes ajustarla levemente si lo justificas, pero mantén /backend y /frontend):

/backend
  /app
    main.py                 # crea FastAPI, monta routers, middlewares
    /core
      settings.py           # env + config (Pydantic Settings)
      security.py           # JWT helpers + dependencies
      logging.py            # logger config
    /api
      router.py             # incluye routers de módulos
    /modules
      /auth
        router.py
        service.py
        schemas.py
      /points
        router.py
        service.py
        schemas.py
      /hw                   # hardware + protocolos (edge)
        drivers.py          # interfaces + selector mock/real
        gpio_mock.py
        gpio_pi.py          # stub con try/except import
        modbus_client.py    # stub cliente modbus tcp
    /tests
      test_health.py
      test_auth.py
  pyproject.toml
  .env.example
  README.md


/frontend
  /src
    main.tsx
    App.tsx                 # layout + router
    /pages
      Login.tsx
      Dashboard.tsx
    /components
      ProtectedRoute.tsx
    /services
      api.ts                # fetch/axios wrapper + token
      auth.ts               # helpers login/logout
    /store
      authStore.ts          # Zustand (simple) o Context
    /types
      point.ts
  vite.config.ts
  package.json
  .env.example
  README.md


--------------------------------------------
B) BACKEND: REQUISITOS TÉCNICOS
1) FastAPI con:
   - Healthcheck: GET /health
   - Auth JWT (mínimo: login fake y dependencia para proteger rutas)
   - Endpoint de ejemplo “points/tags”: GET /api/v1/points (devuelve lista mock)
2) Config por entorno:
   - Pydantic Settings (env vars) con .env
   - Variables: APP_ENV, LOG_LEVEL, JWT_SECRET, JWT_ALGO, API_PREFIX, CORS_ORIGINS
3) Drivers con patrón interfaz + implementación:
   - Interface: IGpioDriver (read/write), ISerialDriver (open/read/write)
   - Implementación Mock para PC (simula valores)
   - Implementación Raspberry (dejar stub con TODO y try/except import)
4) Protocols:
   - Cliente Modbus TCP (stub con estructura y un método “read_holding_registers” simulado)
5) Logging estructurado:
   - logger central en core/logging.py (con formato consistente)
6) Tests:
   - pytest mínimo para /health y para endpoint protegido (401 vs 200)
7) Quality:
   - ruff + black (o ruff format) + mypy (si lo consideras) definidos en pyproject.toml

--------------------------------------------
C) FRONTEND: REQUISITOS TÉCNICOS
1) React + Vite + TypeScript.
2) Routing simple (react-router) con:
   - /login
   - /dashboard
3) Auth:
   - Guard de ruta (si no hay token, redirige a /login)
   - Guardar token en memory o localStorage (explica decisión)
4) API client:
   - axios o fetch wrapper con baseURL desde env
   - Interceptor que adjunte JWT
5) UI mínima:
   - Login form simple
   - Dashboard mostrando:
     - status del backend /health
     - tabla/lista de /api/v1/points
6) Tests:
   - Vitest (mínimo 1 test de componente o del api client)

--------------------------------------------
D) DEV EXPERIENCE
1) Instrucciones claras en README raíz:
   - cómo correr backend
   - cómo correr frontend
   - variables de entorno
2) Modo “PC vs Raspberry”:
   - En backend: seleccionar driver mock/real por APP_ENV o HW_MODE
3) Opcional (si lo incluyes): docker-compose para levantar backend+frontend.

--------------------------------------------
FORMA DE RESPONDER
1) Primero, entrega el árbol de carpetas final.
2) Luego, crea el contenido de los archivos clave (solo lo necesario para arrancar):
   - backend/app/main.py
   - backend/app/core/settings.py
   - backend/app/core/security.py (JWT mínimo)
   - backend/app/api/v1/router.py + endpoints (health, auth, points)
   - backend/app/drivers/interfaces.py + mock.py + raspberry.py(stub)
   - backend/pyproject.toml (deps + ruff/pytest)
   - frontend/src/main.tsx, src/app/App.tsx, router, pages Login/Dashboard
   - frontend/src/services/api.ts
   - frontend/package.json (deps principales)
   - .env.example (backend y frontend)
   - README.md raíz (paso a paso)
3) Mantén el código simple, limpio y comentado donde importe.
4) Si necesitas elegir librerías (state manager, auth storage, etc.), elige una opción razonable y explica en 2-3 líneas.

IMPORTANTE
- No inventes features extra. Solo el scaffold inicial bien planteado.
- Si algo requiere hardware real, debe estar abstracto y el mock debe permitir probar en PC.
- Todo debe compilar/ejecutar con pasos estándar.

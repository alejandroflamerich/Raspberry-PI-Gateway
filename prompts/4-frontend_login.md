Actúa como un Senior Full-Stack Engineer (React/Vite + FastAPI) y diseña/implementa TODA la lógica e interfaz web de login para mi aplicación (para luego acceder a páginas de configuración). Entrega solución completa, segura y testeada.

OBJETIVO
Implementar un sistema de autenticación para una app web con:

- Pantalla de Login.
- Inicialización “primer uso” (si no existe el archivo encriptado de credenciales).
- Recuperación de contraseña por email (reset password).
- Sesión protegida (solo usuarios autenticados pueden entrar a configurar parámetros).
- Persistencia de credenciales en un archivo encriptado en el servidor.

REGLAS CLAVE DE SEGURIDAD (OBLIGATORIAS)

1. NO guardar contraseñas en texto plano.
    - Guardar en el archivo encriptado SOLO:
        - email (username)
        - password_hash (Argon2id o bcrypt con salt)
        - parámetros de hash (si aplica)
        - metadatos mínimos (created_at, updated_at)
2. El archivo debe estar encriptado en reposo (AES-256-GCM o equivalente) y autenticado.
    - La clave de cifrado NUNCA debe estar hardcoded en el repo.
    - Leer la clave desde variable de entorno, por ejemplo: EASYBERRY_AUTH_KEY (base64).
3. Recuperación de contraseña:
    - NO enviar contraseñas por email.
    - Implementar flujo de reset por token:
        - Generar token aleatorio seguro (32+ bytes), con expiración (ej 15 min).
        - Guardar solo hash del token (o token cifrado) y expiración en un archivo encriptado separado o en el mismo.
        - Enviar link por email con token (ej /reset-password?token=...).
        - Al confirmar nueva contraseña, invalidar token.
4. Sesión:
    - Usar cookie httpOnly, secure (en prod), SameSite=Lax/Strict.
    - JWT firmado (HS256/RS256) o session id firmado, con expiración y refresh si aplica.
5. Rate limit / lockout:
    - Bloquear o limitar intentos fallidos (p. ej. 5 intentos / 5 minutos).
6. Validación:
    - El usuario debe ser un email válido.
    - Política mínima de password (>=12 chars, etc).

PRIMER USO (BOOTSTRAP)

- Si el archivo encriptado de credenciales NO existe:
    - La pantalla de login debe ofrecer “Crear cuenta inicial” (solo 1 usuario).
    - Al crear:
        - validar email
        - hashear password
        - guardar en archivo encriptado
    - Luego permitir login normal.
- Si el archivo existe:
    - NO permitir crear otra cuenta desde UI (a menos que se habilite explícitamente luego).

FRONTEND (React + Vite + TS)
Pantallas/Flujos:

1. /login
    - email + password
    - botón “Entrar”
    - link “Olvidé mi contraseña”
    - si backend indica “no existe usuario configurado” -> mostrar CTA “Crear cuenta inicial”
2. /setup (solo primer uso)
    - crear email + password + confirm password
    - botón “Crear”
3. /forgot-password
    - email
    - botón “Enviar enlace de recuperación”
4. /reset-password?token=...
    - new password + confirm
    - botón “Guardar nueva contraseña”
5. Rutas protegidas:
    - /config (placeholder) solo accesible logueado, si no -> redirect a /login
      UX:

- Mostrar errores claros (email inválido, password incorrecto, token expirado, etc).
- Loading states y feedback (toast).
- Validación en cliente + servidor.

BACKEND (FastAPI)
Endpoints requeridos:

- GET /api/auth/status
  -> { configured: bool, authenticated: bool, email?: string }
- POST /api/auth/setup
  -> crea usuario inicial si no existe (solo 1 vez)
- POST /api/auth/login
  -> valida credenciales, crea sesión/cookie
- POST /api/auth/logout
  -> elimina cookie/sesión
- POST /api/auth/forgot
  -> genera token reset y envía email
- POST /api/auth/reset
  -> recibe token + new_password, valida y actualiza password
- GET /api/auth/me
  -> devuelve email si está autenticado

SERVICIOS BACKEND

1. CredentialStore (archivo encriptado):
    - path fijo, por ejemplo: backend/app/data/auth/credentials.enc
    - funciones:
        - is_configured() -> bool
        - create_initial_user(email, password)
        - verify_login(email, password) -> bool
        - set_password(email, new_password)
2. Crypto:
    - AES-256-GCM con nonce aleatorio por escritura
    - serialización JSON interna antes de cifrar
3. Password hashing:
    - Argon2id preferido (passlib[argon2]) o bcrypt (passlib[bcrypt])
4. Email sender:
    - Interfaz IEmailSender con implementación SMTP
    - Variables de entorno: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
    - Modo dev: “console sender” que imprime el link en logs
5. Reset tokens:
    - archivo encriptado tokens.enc o dentro del mismo store
    - guardar hash(token), email, expires_at, used=false

CARPETAS / ARCHIVOS

- frontend/
    - src/
        - pages/Login.tsx
        - pages/Setup.tsx
        - pages/ForgotPassword.tsx
        - pages/ResetPassword.tsx
        - routes/ProtectedRoute.tsx
        - api/authApi.ts
        - utils/validators.ts
- backend/
    - app/
        - main.py
        - routers/auth_router.py
        - services/credential_store.py
        - services/crypto_store.py
        - services/password_hasher.py
        - services/reset_tokens.py
        - services/email_sender.py
        - middleware/auth_session.py
    - data/auth/ (creado runtime, fuera del repo)

TESTS (OBLIGATORIOS)
Backend (pytest):

- Setup:
    - cuando no existe credentials.enc: setup crea archivo y luego configured=true
    - si ya existe: setup devuelve 409 (o 400) “already configured”
- Login:
    - login correcto crea cookie de sesión
    - login incorrecto incrementa contador + rate limit
- Forgot/reset:
    - forgot crea token, envía email (mock sender) con link
    - reset con token válido cambia password
    - reset con token expirado/used -> error
- Encriptación:
    - el archivo guardado NO es JSON legible y se puede descifrar con key correcta
- Todos los tests usan tmp_path (no tocar data real)

Frontend:

- Unit tests (Vitest + Testing Library):
    - render login, validación email
    - flujo “no configured” muestra botón setup
    - manejo de errores de API
- E2E (Playwright):
    - primer uso: ir /login -> setup -> crear -> login -> acceder /config
    - forgot/reset: generar link (modo dev) -> reset -> login con nueva pass

ENTREGABLES

- Código completo y ejecutable:
    - Frontend: npm scripts (dev/test/e2e)
    - Backend: requirements + uvicorn + pytest
- README con:
    - variables de entorno necesarias
    - cómo generar EASYBERRY_AUTH_KEY (base64 32 bytes)
    - cómo correr en modo dev (email a consola) y prod (SMTP real)
- Todo debe pasar tests y permitir ver la UI funcionando en el navegador.

CRITERIOS DE ACEPTACIÓN

- Si no existe credentials.enc: permite crear usuario inicial (email + password) desde UI.
- Login funciona y protege rutas.
- Recuperación de password por email con token (no se envía password).
- Credenciales almacenadas hasheadas + archivo encriptado.
- Tests backend + frontend + e2e pasan.

Prompt: Implementación educativa — EasyberryConnector
Ejecuta este promp.. la implemetacion debes desarrollarla en la ruta backend\app\modules\sw\easyberry

## Objetivo

Desarrollar un módulo backend llamado **EasyberryConnector** que:

- Autentique contra la API REST de Easyberry usando JWT.
- Persista el token en `easyberry_config.json`.
- Construya y envíe payloads (op: `put`) basados en la variable `database` del backend (source of truth).

Este documento está pensado para uso educativo: especifica requisitos, diseño, ejemplos y cómo probar.

## Contexto y archivo de configuración

El proyecto incluye `backend/easyberry_config.json` con esta estructura de ejemplo:

```json
{
	"duration": 20,
	"settings": {
		"url": "https://easyberry-iot.com/wp-json/iot-engine/v2",
		"username": "your_username",
		"password": "your_password",
		"context": "/",
		"token": ""
	},
	"pollers": [
		{
			"things": [
				{ "mbid": "2", "name": "AN-5", "value": 0 },
				{ "mbid": "3", "name": "AN-3", "value": 0 },
				{ "mbid": "4", "name": "AN", "value": 0 },
				{ "mbid": "5", "name": "AN-6", "value": 0 }
			]
		}
	]
}
```

- `settings.token` debe contener el JWT (puede estar vacío inicialmente).
- `settings.url` es el base endpoint; `settings.context` es opcional para componer rutas.

Importante: la fuente de datos real es la variable `database` en memoria del backend. No inventes valores: el conector debe exponer una interfaz para leer `things` desde `database` (por ejemplo `database.getThings()`); para tests provee un stub/mock.

## Requisitos funcionales

1. Config loader

- Funciones: `readConfig()` y `writeConfig(updatedConfig)`.
- Validar la estructura mínima: `settings.url`, `settings.username`, `settings.password`, `settings.token` (token puede estar vacío).
- Escritura atómica: escribir en un temporal y renombrar para evitar corrupción.

2. Login JWT

- Implementar `loginAndPersistToken()`:
    - Si `settings.token` está vacío o las peticiones devuelven 401/403 por token inválido, hacer login con `username`/`password`.
    - Guardar el JWT en `easyberry_config.json` en `settings.token` con `writeConfig()`.
- Manejo de errores y logs:
    - En caso de login fallido, loggear status code y body (sanitizando credenciales).
    - Nunca loggear password ni token completo (enmascarar si es necesario).

3. Envío de datos (PUT `things`)

- Payload esperado (ejemplo):

```json
{
	"op": "put",
	"things": {
		"AN-5": { "value": "25" },
		"AN-3": { "value": "25" },
		"AN": { "value": "25" }
	}
}
```

- Las claves dentro de `things` provienen de `database` (nombre del thing). Los valores deben enviarse como strings.
- Endpoint: construir con `settings.url` y `settings.context` mediante una función `buildEndpoint(config)` (documenta la función y valores por defecto).
- Headers: `Authorization: Bearer <token>`, `Content-Type: application/json`.
- Si recibes 401/403: reintentar una vez, antes de reintentar llamar a `loginAndPersistToken()` y reenviar la petición.
- Si aplica, respetar `duration` para programar envíos periódicos; implementar `runLoop()` o un scheduler simple que envíe cada `duration` segundos.

## Diseño y estructura recomendada

Separar código en capas para testabilidad y claridad:

- `config/`: lectura, validación y escritura de `easyberry_config.json` (incluye `readConfig`/`writeConfig`).
- `auth/`: `loginAndPersistToken()` y lógica relacionada.
- `transport/`: cliente HTTP (wrappers, timeouts, retries, logs sanitizados).
- `connector/`: orquestador que lee `database`, construye payloads y envía.

Recomendaciones:

- Evitar variables globales para el token: leer desde config o mantener un cache en memoria con persistencia explícita.
- Usar tipos (dataclasses en Python o interfaces/types en TS) para los payloads y config.

## Pruebas

Crear tests unitarios e integración mockeada:

- Tests unitarios para:
    - Lectura/escritura atómica de config.
    - Construcción de payload a partir de un `database` simulado.
    - Lógica de reintento cuando el servidor responde 401/403.

- Tests de integración con mocks:
    - Node: `nock` o `msw`.
    - Python: `responses` o `httpx_mock`.

Comprobar en tests que:

- El token se persiste en el JSON.
- Los logs no exponen credenciales ni tokens completos.
- Falta de campo en la config provoca errores claros y bien documentados.

## CLI / Ejecución

Proveer una interfaz de línea de comandos mínima:

- `easyberry-connect --config easyberry_config.json --once` → enviar una vez.
- `easyberry-connect --config easyberry_config.json --loop` → enviar en loop cada `duration` segundos.

El CLI debe devolver códigos de salida adecuados y mensajes legibles para debugging.

## Entregables

- Estructura de carpetas y archivos.
- Implementación del módulo `EasyberryConnector`.
- Tests (unitarios y de integración mockeados).
- `README.md` corto con:
    - Cómo configurar `easyberry_config.json`.
    - Cómo ejecutar en modo `once` y `loop`.
    - Troubleshooting básico (401/403, endpoint, etc.).

## Notas y restricciones

- No hardcodear URLs, usuarios ni contraseñas en el código.
- Declarar dependencias en el manifiesto (`pyproject.toml`, `requirements.txt` o `package.json`).
- Si el mecanismo exacto del endpoint de login no estuviera especificado, permitir parametrizar la ruta mediante `settings.authPath` (valor por defecto razonable) y documentarlo.

## Flujo completo esperado

1. `readConfig()` → 2. `loginAndPersistToken()` (si hace falta) → 3. construir payload desde `database` → 4. enviar (con reintento si 401/403).

## Ejemplos rápidos de uso (CLI)

```bash
# enviar una vez
easyberry-connect --config backend/easyberry_config.json --once

# enviar en loop
easyberry-connect --config backend/easyberry_config.json --loop
```

Este prompt está pensado para ser la especificación educativa y de implementación. Si quieres, puedo:

- Proveer un esqueleto de código en Python o TypeScript siguiendo esta especificación.
- Generar tests de ejemplo (unitarios y de integración mockeados).
- Crear un `README.md` mínimo con instrucciones de ejecución.

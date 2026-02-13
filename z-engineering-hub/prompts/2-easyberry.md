Actúa como un Senior Backend Engineer (Python/FastAPI) y sigue buenas prácticas (SOLID/DRY), tipado, logging y tests.

OBJETIVO
Quiero que el backend cargue la configuración de Easyberry en memoria al iniciar (o al arrancar el módulo), guardándola en una variable compartida llamada `database`. Durante la ejecución de pruebas (y durante el polling real de Modbus), el proceso de polling debe consultar `database.pollers` y, por cada lectura, actualizar el `value` del `thing` correspondiente, haciendo match por `mbid` (Modbus ID).

CONTEXTO / ESTRUCTURA

- Implementar dentro de: `backend/app/modules/sw/easyberry/`
- Asume un modelo de configuración Easyberry que incluye:
    - `database.pollers`: lista de pollers
    - poller contiene `things`
    - thing tiene al menos: `mbid` y `value`

REQUERIMIENTOS FUNCIONALES

1. Cargar configuración en memoria:
    - Implementa un loader/servicio que cargue la configuración Easyberry (desde el origen actual) y la deje disponible en `database`.
    - `database` debe ser accesible desde el módulo de polling.

2. Índice eficiente:
    - Al cargar `database`, construye un índice `mbid -> thing` (y si aplica, `mbid -> (poller, thing)`).
    - En polling NO debe iterar toda la estructura para cada tick.

3. Actualización de valores durante polling:
    - Implementa:
        - `update_thing_value_by_mbid(mbid, new_value, meta=None) -> bool`
    - Debe:
      a) buscar el thing por índice,
      b) actualizar `thing.value = new_value`,
      c) opcional: `thing.updated_at`, `thing.quality/status` si existe,
      d) devolver True si actualizó.

4. Manejo de mbid no encontrado + error.log
    - Si `mbid` no existe en el índice/config:
        - devolver False,
        - además escribir una línea en un archivo `error.log` (append) indicando:
            - timestamp
            - mbid no encontrado
            - contexto opcional: poller actual / slave address / register / función modbus si está disponible
    - Este log debe ser persistente (archivo) y no solo consola.
    - Debe evitar “spam” excesivo:
        - agregar una política simple de deduplicación por ventana (ej: no repetir el mismo mbid cada X segundos) o un contador por mbid.

5. Concurrencia / estabilidad:
    - Polling corre en background; evita condiciones de carrera:
        - usar `threading.Lock` o `asyncio.Lock` según el diseño actual.
    - Si `database` aún no está cargada:
        - loggear warning,
        - no debe explotar.

6. Función/CLI para inspeccionar `database` en profundidad (console)
    - Preparar una función ejecutable desde consola (CLI/entrypoint) para consultar el estado actual del `database` en memoria.
    - Debe permitir pedir rutas como:
        - `database`
        - `database.pollers`
        - `database.pollers[0]`
        - `database.pollers[0].things`
        - `database.pollers[0].things[3].value`
    - Debe imprimir JSON “bonito” (pretty) y soportar límites de profundidad:
        - `--depth N` (ej: depth=1 solo nivel superior)
        - o `--max-items` para listas largas
    - Debe manejar errores de ruta (por ejemplo, índice fuera de rango o atributo inexistente) con mensajes claros.
    - Sugerencia: usar un parser simple de rutas tipo “dot + [index]” y un resolver seguro.

7. Tests
    - Agrega tests unitarios (pytest) para:
        - carga de configuración a `database`
        - construcción de índice `mbid -> thing`
        - `update_thing_value_by_mbid` (encontrado / no encontrado)
        - cuando no encuentra mbid: escribe en `error.log` (usar tmp_path)
        - CLI resolver de rutas (casos válidos e inválidos)
    - Los tests deben correr sin Modbus real (mock del cliente Modbus).

ENTREGABLES

- Código en `backend/app/modules/sw/easyberry/` con:
    - `store.py` (o `database.py`): variable `database`, lock, índice `mbid_index`, helpers
    - `loader.py`: carga/parse de configuración + construcción de índice
    - `polling.py` (o modificación del poller existente): usa `update_thing_value_by_mbid`
    - `error_logger.py` (opcional): writer a `error.log` + dedupe/contador
    - `inspect_cli.py` (o comando en `__main__.py`): CLI para inspección por ruta y profundidad
    - tests en la carpeta de tests del backend, incluyendo validación de `error.log` y del resolver

CRITERIOS DE ACEPTACIÓN

- Al iniciar el módulo, `database` queda poblada con la config y el índice está listo.
- Durante el polling, cada lectura Modbus actualiza el `thing.value` correcto por `mbid`.
- Si llega un `mbid` no definido:
    - devuelve False,
    - genera/append en `error.log` con timestamp y mbid.
- El CLI permite consultar cualquier sub-ruta pedida e imprime JSON.
- Los tests pasan y no requieren Modbus real.

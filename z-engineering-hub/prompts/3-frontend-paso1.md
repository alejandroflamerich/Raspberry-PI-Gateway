Actúa como un Senior Full-Stack Engineer (React/Vite + FastAPI). Entrega una solución completa, funcional y testeada.

OBJETIVO
Construir una UI web para ver y editar 2 archivos JSON del servidor:

- easyberry_config.json (columna izquierda)
- polling_config.json (columna derecha)

REQUISITOS UI/UX

1. Layout:
    - Pantalla con 2 columnas (50/50 o responsivo):
        - Izquierda: easyberry_config.json
        - Derecha: polling_config.json
    - Encabezados claros por columna + estado (Loaded / Dirty / Saved / Error)

2. Editors:
    - Cada JSON debe mostrarse en un editor tipo “pretty print”.
    - Al cargar:
        - el contenido se presenta formateado (indent=2).
    - Al perder foco (blur) en cada editor:
        - si el contenido es JSON válido -> auto formatear a pretty print JSON y mantener el cursor lo mejor posible.
        - si el contenido NO es JSON válido -> NO formatear, mostrar error de validación debajo del editor (con línea/columna si es posible).

3. Guardado:
    - Botón “Guardar” por cada archivo (o un botón “Guardar ambos” + individual también es válido).
    - Al guardar:
        - enviar el JSON al backend,
        - el backend valida JSON,
        - persiste en el archivo correspondiente en el servidor,
        - respuesta clara de éxito/error.
    - No permitir guardar si hay JSON inválido.
    - Mostrar confirmación (toast / badge) “Guardado correctamente”.

4. Robustez:
    - Manejar errores de red.
    - Loading states.
    - Confirmación si hay cambios sin guardar y el usuario intenta recargar/navegar.

TECNOLOGÍA
Frontend:

- React + Vite + TypeScript
- Para el editor: usar Monaco Editor (preferido) o CodeMirror 6 (aceptable).
- Debe soportar:
    - syntax highlighting JSON
    - line numbers
    - auto indentation
    - tamaño del editor adaptable (altura al viewport)

Backend:

- FastAPI (o el backend existente si ya lo tienes; si no, crea uno mínimo).
- Endpoints REST:
    - GET /api/config/easyberry -> devuelve JSON del archivo easyberry_config.json
    - PUT /api/config/easyberry -> valida y guarda easyberry_config.json
    - GET /api/config/polling -> devuelve JSON del archivo polling_config.json
    - PUT /api/config/polling -> valida y guarda polling_config.json
- Validación:
    - Rechazar si JSON inválido.
    - Guardar con pretty print (indent=2, sort_keys=false).
- Seguridad mínima:
    - Evitar path traversal (nombres fijos, no se aceptan rutas del cliente).
- Ubicación de archivos:
    - define un directorio fijo, por ejemplo: backend/app/data/config/
    - archivos: easyberry_config.json y polling_config.json

ARQUITECTURA / CARPETAS

- frontend/
    - src/
        - pages/ConfigEditorPage.tsx
        - components/JsonEditorPanel.tsx
        - api/configApi.ts
        - utils/jsonFormat.ts (parse/pretty/validation)
- backend/
    - app/
        - main.py
        - routers/config_router.py
        - services/config_files.py
        - data/config/easyberry_config.json
        - data/config/polling_config.json

DETALLES IMPORTANTES DE IMPLEMENTACIÓN

- Pretty print en blur:
    - Implementa `formatOnBlur(editorText) => { formattedText, error }`
    - Si error: mostrar mensaje sin romper el editor.
- Dirty tracking:
    - Marcar “dirty” si el contenido cambia vs el último guardado.
    - Deshabilitar botón Guardar si no hay cambios.
- Guardar:
    - Al guardar exitoso:
        - actualizar “lastSavedText” y limpiar dirty.

TESTS (OBLIGATORIOS)

1. Backend (pytest):
    - GET devuelve JSON válido.
    - PUT guarda y el archivo queda en disco con formato indent=2.
    - PUT con JSON inválido devuelve 400 y NO escribe archivo.
    - Tests usando tmp_path (no tocar archivos reales).

2. Frontend:
    - Unit tests (Vitest + Testing Library):
        - renderiza dos paneles.
        - si el usuario edita y blur con JSON válido -> se formatea.
        - blur con JSON inválido -> muestra error y NO formatea.
        - botón guardar se habilita/deshabilita según dirty/validez.
    - E2E (Playwright):
        - abrir la página, verificar que ambos JSON cargan y se muestran.
        - editar uno, blur -> auto pretty print.
        - guardar -> ver confirmación y recargar -> persiste.
        - introducir JSON inválido -> error visible y guardar bloqueado.

ENTREGABLES

- Código completo listo para correr local:
    - scripts: `npm install`, `npm run dev`, `npm test`, `npx playwright test`
    - backend: `pip install -r requirements.txt`, `pytest`, `uvicorn app.main:app --reload`
- Instrucciones de ejecución en README.
- Asegúrate de “hasta que todo esté conforme para mirar en el navegador”: debe correr y pasar tests.

CRITERIOS DE ACEPTACIÓN

- Se ven ambos archivos a la vez (2 columnas).
- Se formatea a pretty print al perder foco si es JSON válido.
- Se muestra error si JSON inválido y no permite guardar.
- Guardar persiste en servidor y al recargar se mantiene.
- Tests pasan (backend + frontend + e2e).

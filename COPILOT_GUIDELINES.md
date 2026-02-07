# Copilot Guidelines — Edge Project (FastAPI + React/Vite)

Propósito
- Informar a GitHub Copilot / asistentes de código sobre el tipo de proyecto y las prácticas esperadas.
- Dirigir la generación de código hacia implementaciones tipadas, testeables, seguras y fácilmente desplegables en PC y Raspberry Pi.

Cómo usar esta guía
- Antes de generar código, revisa la carpeta `skills/` y aplica las recomendaciones relevantes.
- Prefiere soluciones simples y explícitas sobre la sobre-ingeniería.
- Mantén los nombres claros y consistentes con la arquitectura: `backend/app`, `frontend/src`.

Reglas generales
- Tipado primero: en Python usa tipos y Pydantic; en frontend usa TypeScript.
- Tests obligatorios para nuevas funciones públicas (pytest / vitest).
- Separación de responsabilidades: core/config, api, modules, modules/hw (drivers), tests.
- No incluir secretos en el código — usa `.env` y `Settings`.
- Para hardware o protocolos no disponibles en el entorno: generar mocks y adaptadores.

Workflow de generación
1. Identifica la skill relevante en `skills/` (ej.: `python_fastapi.md` para endpoints backend).
2. Genera una implementación mínima y un test asociado.
3. Añade documentación breve y actualización a `README.md` si procede.
4. Ejecuta linters y pruebas localmente (o sugiere los comandos).

Commit & PR
- Generaciones grandes deben dividirse en commits lógicos: "feat(api): add points endpoint (mock)".
- Añadir tests y actualizar README en el mismo cambio cuando sea necesario.

Referencias de skills
- Consulta `skills/` para instrucciones concretas y snippets por tipo de tarea.

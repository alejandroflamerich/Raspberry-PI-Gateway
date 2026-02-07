Skill: Python + FastAPI

Cuando usar
- Crear endpoints, servicios backend, dependencias y configuración.

Objetivo
- API REST ligera, tipada y testeable; configurada por entornos; compatible con ejecución en Raspberry Pi.

Buenas prácticas
- Usar Pydantic para `settings` y `schemas`.
- Implementar routers por dominio `api/v1/<module>` y montar en `app.main`.
- Dependencias inyectables (FastAPI `Depends`) para seguridad y drivers.
- Evitar lógica de negocio en handlers; delegar a `service`.

Patrones y snippets
- Settings:
  - `class Settings(BaseSettings): ...` con `env_file`. Importar `settings = Settings()`.
- Endpoint básico:
```py
@router.get('/health')
async def health():
    return {'status': 'ok'}
```

Tests
- Escribir `TestClient` con casos para 200/401.

Checklist
- [ ] Tipos y Pydantic schemas
- [ ] Tests para rutas públicas y protegidas
- [ ] Logging adecuado en errores

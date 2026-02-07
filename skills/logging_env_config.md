Skill: Logging & Environment Configuration

Cuando usar
- Configurar logs estructurados y gestionar configuración por entornos.

Buenas prácticas
- Centralizar configuración de logging en `core/logging.py`.
- Usar `Settings` (Pydantic BaseSettings) y `.env` para entornos.
- No imprimir secretos en logs.

Patrón
- `configure_logging()` que lea `settings.log_level`.
- `Settings` con `env_file` y validación de variables críticas.

Checklist
- [ ] Logger centralizado
- [ ] .env ejemplos y validación de settings

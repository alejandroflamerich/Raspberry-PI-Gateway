Skill: Linting, Formatting & Typing

Cuando usar
- Mantener calidad de código y coherencia entre desarrolladores.

Buenas prácticas
- Usar `ruff` y `black` para Python; `eslint`/`prettier` opcional para frontend.
- Añadir `mypy` o `pyright` para chequeo de tipos si el proyecto crece.
- Configurar reglas en `pyproject.toml` y `package.json`.

Checklist
- [ ] `black` para formateo
- [ ] `ruff` para lint
- [ ] `mypy` o `pyright` si se añade tipado estático

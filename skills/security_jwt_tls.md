Skill: Security (JWT, TLS)

Cuando usar
- Autenticación/Autorización y comunicación segura.

Buenas prácticas
- No hardcodear `JWT_SECRET`; usar `Settings` y `.env`.
- Tokens: corta expiración y validar correctamente `exp`.
- Usar HTTPS/TLS para comunicaciones en producción; en dev usar TLS terminator o ngrok si se necesita.

Patrones
- Crear helpers `create_access_token`, `decode_token` y dependencia `get_current_user`.

Checklist
- [ ] `JWT_SECRET` en env
- [ ] Dependencias que validen token y respondan 401

Skill: Docker & CI (dev workflow)

Cuando usar
- Encapsular backend/frontend para desarrollo reproducible y para despliegue en servidores o Pi (multi-arch).

Buenas prácticas
- Dockerfiles sencillos para dev; optimizar imágenes para producción y ARM separadamente.
- `docker-compose` para levantar servicios locales.
- Añadir pipeline CI que instale deps, corra linters y tests.

Checklist
- [ ] Dockerfile backend y frontend
- [ ] docker-compose.yml para dev
- [ ] CI config (GitHub Actions) que corra linters y tests

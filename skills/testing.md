Skill: Testing (pytest / vitest)

Cuando usar
- Escribir pruebas unitarias y de integración ligeras para backend y frontend.

Buenas prácticas
- Backend: pytest + TestClient; tests en `backend/tests/`.
- Frontend: Vitest para funciones y pequeños componentes.
- Mockear dependencias externas (HW drivers, Modbus) para tests en PC.

Patrones
- Arrange / Act / Assert
- Fixtures para TestClient y datos comunes

Checklist
- [ ] Tests para endpoints críticos: auth, health, points
- [ ] Mocks para hardware

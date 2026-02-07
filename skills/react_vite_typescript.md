Skill: React + Vite + TypeScript

Cuando usar
- Implementar la interfaz del usuario, rutas y consumos de API.

Objetivo
- UI ligera con routing y cliente HTTP; protección de rutas mediante token.

Buenas prácticas
- Usar TypeScript para componentes, props y tipos de API (`types/`).
- Mantener `services/api.ts` con wrapper axios/fetch y manejo de token.
- Guardas tokens en `localStorage` para persistencia mínima; preferir HttpOnly cookies en producción.
- Componentes pequeños y testables; páginas en `pages/`.

Patrones y snippets
- API client:
```ts
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL })
api.interceptors.request.use(cfg => {...})
```
- Protected route: componente que redirige si no hay token.

Tests
- Usar Vitest para tests de componentes y mocks de `services/api`.

Checklist
- [ ] Tipos en `src/types` para respuestas del backend
- [ ] Test mínimo para `services/api` o un componente

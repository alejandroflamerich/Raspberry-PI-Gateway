1. Preparar (en tu laptop)

    # iniciar sesión en Docker Hub (o tu registry)
    docker login

    # crear/usar un builder buildx (una sola vez)
    docker buildx create --use
    

2. Opción A — Publicar multi-arch en Docker Hub (recomendado)
    Backend:
    # desde c:\... \proyecto-final\backend
    docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t YOUR_DOCKERHUB_USER/edge-backend:latest --push .
    
    Frontend:
    # desde c:\... \proyecto-final\frontend
    docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 -t YOUR_DOCKERHUB_USER/edge-frontend:latest --push .

docker buildx inspect --bootstrap
    En la Raspberry:
    # desde la Raspberry, tirar las imágenes y levantar
    docker pull YOUR_DOCKERHUB_USER/edge-backend:latest
    docker pull YOUR_DOCKERHUB_USER/edge-frontend:latest
    # actualizar docker-compose.yml para usar esas imágenes o ejecutar:
    docker compose --pull
    docker compose up -d 
    docker compose up -d --no-build --force-recreate


Correr el docker en la maquina local
1. Preparar configs (no commitear)
    copy .env.example .env
    copy backend\easyberry_config.example.json backend\easyberry_config.json
    notepad .env
    notepad backend\easyberry_config.json

2. Construir y levantar con Docker Compose
    # construir y levantar (usa la imagen adecuada en tu laptop)
    docker compose build --no-cache
    docker compose up -d --build

3. Ver estado y logs
    docker compose ps
    docker ps

    # logs generales
    docker compose logs -f

    # logs por servicio
    docker compose logs backend --tail 200 --follow
    docker compose logs frontend --tail 200 --follow

4. Probar endpoints / UI
    # backend health
    curl http://localhost:8000/api/v1/health

    # abrir frontend en el navegador
    start http://localhost:5173

    # probar login (backend actualmente usa user=admin password=Admin2026)
    curl -i -X POST http://localhost:8000/api/v1/auth/login `
    -H "Content-Type: application/json" `
    -d '{"username":"admin","password":"Admin2026"}'

5. Detener y limpiar
    # detener y eliminar contenedores creados por compose
    docker compose down

    # eliminar imágenes locales creadas por build (opcional)
    docker image ls | Select-String "raspberry-pi-gateway|edge-backend|edge-frontend"
    # limpiar space (opcional, con cuidado)
    docker system prune --all --volumes
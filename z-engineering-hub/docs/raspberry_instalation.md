# Instalación y despliegue en Raspberry Pi

Este documento describe pasos sencillos para clonar, preparar y desplegar el proyecto en una Raspberry Pi usando Docker Compose. Se asume que tienes acceso por SSH y permisos sudo.

## Requisitos previos

- Conexión a Internet en la Raspberry.
- `git` instalado.
- `curl` disponible (para instalar Docker si hace falta).

## 1. Clonar el repositorio
Desde el usuario de la Raspberry, crea una carpeta para proyectos y clona el repo:

```bash
cd ~
mkdir -p projects
cd projects
git clone https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git
cd Raspberry-PI-Gateway
```

## 2. Verificar que estás en la raíz del proyecto
Comprueba que los archivos principales existen:

```bash
pwd
ls -la
# ver docker-compose.yml si existe
[ -f docker-compose.yml ] && echo "docker-compose.yml OK" || echo "No hay docker-compose.yml"
# comprobar Dockerfiles
[ -f backend/Dockerfile ] && echo "backend/Dockerfile OK" || echo "No backend/Dockerfile"
[ -f frontend/Dockerfile ] && echo "frontend/Dockerfile OK" || echo "No frontend/Dockerfile"
```

## 3. Instalar Docker (si no está presente)
Comprueba la versión y, si falta, usa el instalador oficial:

```bash
docker --version || (curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $USER && newgrp docker)
```

Después de añadir el usuario al grupo `docker` puede que necesites reconectar la sesión o ejecutar `newgrp docker` para aplicar el cambio.

## 4. Instalar `docker-compose` (si es necesario)
Si tu sistema no provee `docker compose` nativo, instala la utilidad clásica mediante `pip`:

```bash
docker-compose --version || (sudo apt update && sudo apt install -y python3-pip && sudo pip3 install docker-compose)
```

Nota: en sistemas recientes `docker compose` (sin guion) ya viene incluido en el paquete Docker.

## 5. Construir y arrancar la aplicación con Docker Compose
Desde la raíz del repositorio:

```bash
# construir y levantar en segundo plano
docker compose up -d --build

# ver estado de servicios
docker compose ps

# ver logs en tiempo real (útil para diagnosticar errores)
docker compose logs -f
```

Si un contenedor falla, copia aquí los logs (`docker-compose logs <service>`) y te ayudaré a diagnosticarlo.

### 5.1 Arrancar / reiniciar servicios con Docker
Comandos útiles para gestionar los servicios:

```bash
# levantar todos los servicios (build si hay cambios)
docker compose up -d --build

# levantar/reconstruir sólo el backend
docker compose up -d --build backend

# ver estado
docker compose ps

# ver logs en tiempo real de un servicio
docker compose logs backend --follow
docker compose logs frontend --follow

# parar servicios
docker compose down
```

> Nota: usamos `docker compose` (plugin moderno). El binario legacy `docker-compose` puede no estar instalado.

### 5.2 Arrancar en local (modo desarrollo, sin Docker)
Si prefieres ejecutar los servicios en la Raspberry sin contenedores (útil para debugging), sigue estos pasos.

Backend (Python / FastAPI):

```bash
cd backend
# crear/activar venv
python3 -m venv .venv
source .venv/bin/activate

# instalar dependencias (usa pyproject/requirements según tu proyecto)
pip install --upgrade pip
pip install -r requirements.txt   # o: pip install -e .

# arrancar servidor de desarrollo
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend (Vite / React):

```bash
cd frontend
npm install
# arrancar en modo desarrollo (accesible en la red con --host)
npm run dev -- --host 0.0.0.0

# para producción: build + servir la carpeta `dist`
npm run build
# servir con un pequeño servidor estático (ej. `serve`)
npx serve -s dist -l 80
```

## 5.3 Archivos de configuración y seguridad
Antes de arrancar los servicios asegúrate de crear los archivos de configuración locales a partir de los ejemplos y no cometer credenciales al repositorio:

```bash
# en la raíz del repo
cp .env.example .env
cp backend/easyberry_config.example.json backend/easyberry_config.json
# editar los ficheros con credenciales/valores reales
```

No hagas `git add`/`git commit` de `backend/easyberry_config.json` ni de `.env`. Si accidentalmente subiste credenciales, rota los secretos y elimina el archivo del historial git.

## 6. Probar los endpoints desde la Raspberry

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost/    # frontend (si expone en 80)
```

## 7. Actualizar código y redeploy
Para actualizar el código y reconstruir los contenedores:

```bash
cd ~/projects/Raspberry-PI-Gateway
git pull origin main
docker-compose up -d --build
```

## Nota sobre entornos Python y el error "externally-managed-environment"
Si al instalar dependencias con `pip` ves un error similar a "externally-managed-environment" (PEP 668), significa que el intérprete está gestionado por el sistema operativo y `pip` evita modificar paquetes globales. Recomendaciones:

- Usar un entorno virtual (`venv`) antes de `pip install`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

- O bien evitar instalaciones locales y confiar en Docker (recomendado para despliegue), ya que los contenedores instalan dependencias en su propio entorno aislado.

- Como último recurso y con precaución, puedes usar `--break-system-packages` con `pip` para forzar la instalación, pero esto puede romper paquetes gestionados por el sistema.

## ¿Quieres que añada más detalles?
Puedo:

- Incluir instrucciones para crear y rellenar los archivos de configuración `backend/easyberry_config.json` y `.env` a partir de ejemplos.
- Añadir un pequeño servicio `systemd` para arrancar `docker-compose` al iniciar la Raspberry.

Archivo editado: `docs/raspberry_instalation.md`
# Desplegar la aplicación en Raspberry Pi

Este documento describe pasos prácticos para subir y ejecutar la app (backend FastAPI + frontend Vite/React) en un Raspberry Pi. Incluye dos enfoques: recomendado con Docker Compose y un método manual sin contenedores.

---

## Requisitos previos en la Raspberry

- Raspberry Pi OS (64-bit recomendado) o Debian compatible
- Al menos 1 GB RAM (mejor 2GB+), red y SSH habilitado
- Acceso SSH o terminal local
- Git instalado (`sudo apt update && sudo apt install -y git`) si vas a clonar el repositorio

Opcional (si usas Docker, recomendado): Docker y Docker Compose

Instalar Docker (comando oficial):

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Cierra sesión / vuelve a iniciar para aplicar el grupo docker
```

Instalar Docker Compose plugin (si no viene con Docker):

```bash
sudo apt install -y libffi-dev libssl-dev
sudo apt install -y python3 python3-pip
sudo pip3 install docker-compose
```

---

## Opción A — (Recomendada) Usar Docker Compose

1. Clona el repo en la Raspberry (o copia el código):

```bash
cd /home/pi
git clone https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git
cd Raspberry-PI-Gateway
```

2. Configura variables de entorno / archivos `.env` si tu `docker-compose.yml` los referencia. Por ejemplo crea `.env` en la raíz con las variables necesarias (puede variar según tu configuración):

```text
# ejemplo .env
API_PORT=8000
EASYBERRY_URL=http://...
# otros valores específicos de tu app
```

3. Construir y levantar los servicios con Docker Compose:

```bash
# si tienes docker-compose.yml en la raíz
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart
```

4. Comprobar servicios:

```bash
docker ps
docker-compose ps
```

Ventajas: aislamiento, despliegue reproducible y fácil rollback.

---

## Opción B — Instalación manual (sin Docker)

Nota: este flujo es más frágil y depende de las dependencias del proyecto. Úsalo si no quieres usar contenedores.

1. Clonar el repo:

```bash
cd /home/pi
git clone https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git
cd Raspberry-PI-Gateway
```

2. Backend (Python / FastAPI)

- Instala Python 3.10/3.11 y pip:

```bash
sudo apt install -y python3 python3-venv python3-pip
```

- Crear entorno virtual e instalar dependencias (ajusta si usas `pyproject.toml` / poetry):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
# Si tienes requirements.txt
pip install -r requirements.txt
# o si usas poetry: pip install poetry && poetry install
```

- Ejecutar uvicorn (ejemplo):

```bash
export PYTHONPATH=$(pwd)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

- Para producción, crea un `systemd` service para uvicorn (ejemplo abajo).

3. Frontend (build estático)

- Instalar Node.js y npm (versión 16+ recomendada):

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

- Construir la app estática:

```bash
cd frontend
npm install
npm run build
# salida en dist/ (o carpeta configurada)
```


```bash

1. **Instalar Docker y Docker Compose**: Asegúrate de que Docker y Docker Compose están instalados en tu Raspberry Pi. Puedes seguir los pasos en la sección de requisitos previos.

2. **Crear un archivo `docker-compose.yml`**: En la raíz de tu proyecto, crea un archivo llamado `docker-compose.yml`. Este archivo define los servicios que tu aplicación necesita. Aquí hay un ejemplo básico:

```yaml
version: '3'
services:
  app:
    image: tu_imagen:latest
    ports:
      - "8000:8000"
    environment:
      - API_PORT=8000
```

3. **Levantar los servicios**: Desde la raíz de tu proyecto, ejecuta el siguiente comando para construir y levantar los servicios definidos en tu `docker-compose.yml`:

```bash
docker-compose up -d
```

4. **Verificar que los servicios están corriendo**: Puedes usar el siguiente comando para ver el estado de tus contenedores:

```bash
docker-compose ps
```

5. **Acceder a tu aplicación**: Abre un navegador y dirígete a `http://<RASPBERRY_IP>:8000` para ver tu aplicación en funcionamiento.

6. **Detener los servicios**: Cuando termines, puedes detener los servicios con el siguiente comando:

```bash
docker-compose down
```

Si quieres, genero un `docker-compose.yml` final listo para tu repo y opcionalmente un `systemd` unit (ya hay ejemplo). ¿Deseas que lo añada al repo y haga un commit sugerido? 
# instalar nginx
sudo apt install -y nginx
# configurar un bloque de servidor que sirva la carpeta 'frontend/dist'
```

4. Ejemplo `systemd` para backend (uvicorn)

Crear archivo `/etc/systemd/system/gateway-backend.service` con contenido:

```ini
[Unit]
Description=Gateway Backend (uvicorn)
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/Raspberry-PI-Gateway/backend
Environment=PATH=/home/pi/Raspberry-PI-Gateway/backend/.venv/bin
ExecStart=/home/pi/Raspberry-PI-Gateway/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

Recargar systemd y arrancar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gateway-backend.service
sudo journalctl -u gateway-backend.service -f
```

5. Firewall / red

Abre puertos si necesitas (ej. 80/nginx, 8000 API):
# Desplegar la aplicación en Raspberry Pi

Este documento describe pasos prácticos para subir y ejecutar la app (backend FastAPI + frontend Vite/React) en un Raspberry Pi. Incluye dos enfoques: recomendado con Docker Compose y un método manual sin contenedores.

---

## Requisitos previos en la Raspberry

- Raspberry Pi OS (64-bit recomendado) o Debian compatible
- Al menos 1 GB RAM (mejor 2GB+), red y SSH habilitado
- Acceso SSH o terminal local
- Git instalado (`sudo apt update && sudo apt install -y git`) si vas a clonar el repositorio

Opcional (si usas Docker, recomendado): Docker y Docker Compose

Instalar Docker (comando oficial):

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Cierra sesión / vuelve a iniciar para aplicar el grupo docker
```

Instalar Docker Compose plugin (si no viene con Docker):

```bash
sudo apt install -y libffi-dev libssl-dev
sudo apt install -y python3 python3-pip
sudo pip3 install docker-compose
```

---

## Opción A — (Recomendada) Usar Docker Compose

1. Clona el repo en la Raspberry (o copia el código):

```bash
cd /home/pi
git clone https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git
cd Raspberry-PI-Gateway
```

2. Configura variables de entorno / archivos `.env` si tu `docker-compose.yml` los referencia. Por ejemplo crea `.env` en la raíz con las variables necesarias (puede variar según tu configuración):

```text
# ejemplo .env
API_PORT=8000
EASYBERRY_URL=http://...
# otros valores específicos de tu app
```

3. Construir y levantar los servicios con Docker Compose:

```bash
# si tienes docker-compose.yml en la raíz
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Reiniciar
docker-compose restart
```

4. Comprobar servicios:

```bash
docker ps
docker-compose ps
```

Ventajas: aislamiento, despliegue reproducible y fácil rollback.

---

## Opción B — Instalación manual (sin Docker)

Nota: este flujo es más frágil y depende de las dependencias del proyecto. Úsalo si no quieres usar contenedores.

1. Clonar el repo:

```bash
cd /home/pi
git clone https://github.com/alejandroflamerich/Raspberry-PI-Gateway.git
cd Raspberry-PI-Gateway
```

2. Backend (Python / FastAPI)

- Instala Python 3.10/3.11 y pip:

```bash
sudo apt install -y python3 python3-venv python3-pip
```

- Crear entorno virtual e instalar dependencias (ajusta si usas `pyproject.toml` / poetry):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
# Si tienes requirements.txt
pip install -r requirements.txt
# o si usas poetry: pip install poetry && poetry install
```

- Ejecutar uvicorn (ejemplo):

```bash
export PYTHONPATH=$(pwd)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

- Para producción, crea un `systemd` service para uvicorn (ejemplo abajo).

3. Frontend (build estático)

- Instalar Node.js y npm (versión 16+ recomendada):

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

- Construir la app estática:

```bash
cd frontend
npm install
npm run build
# salida en dist/ (o carpeta configurada)
```


```bash

1. **Instalar Docker y Docker Compose**: Asegúrate de que Docker y Docker Compose están instalados en tu Raspberry Pi. Puedes seguir los pasos en la sección de requisitos previos.

2. **Crear un archivo `docker-compose.yml`**: En la raíz de tu proyecto, crea un archivo llamado `docker-compose.yml`. Este archivo define los servicios que tu aplicación necesita. Aquí hay un ejemplo básico:

```yaml
version: '3'
services:
  app:
    image: tu_imagen:latest
    ports:
      - "8000:8000"
    environment:
      - API_PORT=8000
```

3. **Levantar los servicios**: Desde la raíz de tu proyecto, ejecuta el siguiente comando para construir y levantar los servicios definidos en tu `docker-compose.yml`:

```bash
docker-compose up -d
```

4. **Verificar que los servicios están corriendo**: Puedes usar el siguiente comando para ver el estado de tus contenedores:

```bash
docker-compose ps
```

5. **Acceder a tu aplicación**: Abre un navegador y dirígete a `http://<RASPBERRY_IP>:8000` para ver tu aplicación en funcionamiento.

6. **Detener los servicios**: Cuando termines, puedes detener los servicios con el siguiente comando:

```bash
docker-compose down
```

Si quieres, genero un `docker-compose.yml` final listo para tu repo y opcionalmente un `systemd` unit (ya hay ejemplo). ¿Deseas que lo añada al repo y haga un commit sugerido? 
# instalar nginx
sudo apt install -y nginx
# configurar un bloque de servidor que sirva la carpeta 'frontend/dist'
```

4. Ejemplo `systemd` para backend (uvicorn)

Crear archivo `/etc/systemd/system/gateway-backend.service` con contenido:

```ini
[Unit]
Description=Gateway Backend (uvicorn)
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/home/pi/Raspberry-PI-Gateway/backend
Environment=PATH=/home/pi/Raspberry-PI-Gateway/backend/.venv/bin
ExecStart=/home/pi/Raspberry-PI-Gateway/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

Recargar systemd y arrancar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gateway-backend.service
sudo journalctl -u gateway-backend.service -f
```

5. Firewall / red

Abre puertos si necesitas (ej. 80/nginx, 8000 API):

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

---

## Transferir archivos desde tu máquina (si no usas git clone)

Usa `scp` o `rsync`:

```bash
# desde tu máquina local
scp -r ./Raspberry-PI-Gateway pi@<RASPBERRY_IP>:/home/pi/
# o con rsync (más eficiente)
rsync -avz --progress ./Raspberry-PI-Gateway pi@<RASPBERRY_IP>:/home/pi/
```

---

## Comandos útiles de verificación

- Ver logs Docker Compose:
  `docker-compose logs -f`
- Ver logs systemd del backend:
  `sudo journalctl -u gateway-backend.service -f`
- Probar endpoints:
  `curl http://<RASPBERRY_IP>:8000/api/v1/health` (ajusta ruta)

---

## Notas y recomendaciones

- Si vas a usar la Raspberry en producción, usa Docker Compose para evitar problemas de dependencias.
- Mantén copias de seguridad de tus `.env` y secretos fuera del repositorio si son sensibles.
- Usa `--force-with-lease` con cuidado si fuerzas pushes desde tu máquina; no es necesario para despliegues.

Si quieres, puedo añadir un ejemplo de `docker-compose.yml` específico o un `systemd` y `nginx` config adaptado a este repo — dime cuál prefieres y lo genero.

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
```

---

## Transferir archivos desde tu máquina (si no usas git clone)

Usa `scp` o `rsync`:

```bash
# desde tu máquina local
scp -r ./Raspberry-PI-Gateway pi@<RASPBERRY_IP>:/home/pi/
# o con rsync (más eficiente)
rsync -avz --progress ./Raspberry-PI-Gateway pi@<RASPBERRY_IP>:/home/pi/
```

---

## Comandos útiles de verificación

- Ver logs Docker Compose:
  `docker-compose logs -f`
- Ver logs systemd del backend:
  `sudo journalctl -u gateway-backend.service -f`
- Probar endpoints:
  `curl http://<RASPBERRY_IP>:8000/api/v1/health` (ajusta ruta)

---

## Notas y recomendaciones

- Si vas a usar la Raspberry en producción, usa Docker Compose para evitar problemas de dependencias.
- Mantén copias de seguridad de tus `.env` y secretos fuera del repositorio si son sensibles.
- Usa `--force-with-lease` con cuidado si fuerzas pushes desde tu máquina; no es necesario para despliegues.

Si quieres, puedo añadir un ejemplo de `docker-compose.yml` específico o un `systemd` y `nginx` config adaptado a este repo — dime cuál prefieres y lo genero.

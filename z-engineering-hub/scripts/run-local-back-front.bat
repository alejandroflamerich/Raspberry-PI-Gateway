@echo off
setlocal enableextensions enabledelayedexpansion





































exit /b 0endlocalecho Hecho.:end
:: fingoto end)    echo Cancelado por usuario. Ningún proceso fue detenido.) else (    echo Intento de parada completado.    taskkill /F /IM python.exe 1>nul 2>nul    taskkill /F /IM node.exe 1>nul 2>nul    echo Matando node.exe y python.exe (forzoso)...if /i "%CONFIRM%"=="y" (set /p CONFIRM=Continuar y matar procesos node/python? (y/N) => echo Parando procesos locales (node/python)...
:downgoto endecho - Para detener, ejecuta este script y elige "down".echo Backend y frontend iniciados en ventanas separadas.popdstart "easyberry-frontend" cmd /k "cd /d "%~dp0\..\frontend" && npm run dev -- --host 0.0.0.0"REM Frontend: abre nueva ventana y arranca Vitestart "easyberry-backend" cmd /k "cd /d "%~dp0\..\backend" && if exist .venv\Scripts\Activate.bat (call .venv\Scripts\Activate.bat) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"REM Backend: abre nueva ventana y activa .venv si existepushd "%~dp0\.."echo Iniciando backend y frontend (local)...
:upgoto ask_actionecho Opción no válida. Escribe "up" o "down".if /i "%ACTION%"=="down" goto downif /i "%ACTION%"=="up" goto upset /p ACTION=> echo ¿Deseas arrancar o parar los servicios localmente? (up/down)set "ACTION=":ask_action
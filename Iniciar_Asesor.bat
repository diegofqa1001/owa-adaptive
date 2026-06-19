@echo off
title Asesor OWA Adaptativo - Instalacion y arranque
cd /d "D:\Downloads\repo_OWA"

echo ============================================================
echo   ASESOR OWA ADAPTATIVO - Tesis Doctoral
echo ============================================================
echo.
echo [1/3] Verificando Python...
python --version
if errorlevel 1 (
  echo.
  echo  ERROR: Python no esta instalado o no esta en el PATH.
  echo  Instala Python 3.9 o superior desde https://www.python.org/downloads/
  echo  y marca la casilla "Add Python to PATH" durante la instalacion.
  echo.
  pause
  exit /b 1
)

echo.
echo [2/3] Instalando dependencias (puede tardar 1-2 minutos la primera vez)...
python -m pip install --upgrade pip
python -m pip install -e ".[all]"
if errorlevel 1 (
  echo.
  echo  ERROR instalando dependencias. Revisa el mensaje de arriba.
  echo.
  pause
  exit /b 1
)

echo.
echo [3/3] Abriendo el asistente en tu navegador...
echo  (Para cerrarlo luego, cierra esta ventana negra.)
echo.
python -m streamlit run app/streamlit_app.py

pause

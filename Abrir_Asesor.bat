@echo off
title Asesor OWA Adaptativo
cd /d "D:\Downloads\repo_OWA"

REM Evitar el mensaje de correo del primer arranque de Streamlit.
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  >"%USERPROFILE%\.streamlit\credentials.toml" echo [general]
  >>"%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

echo Abriendo el asistente en http://localhost:8501 ...
echo (Deja esta ventana abierta mientras usas el asistente.)
python -m streamlit run app/streamlit_app.py --server.headless=true --browser.gatherUsageStats=false

pause

@echo off
rem Launch Voice Studio. Works from any folder location.
set "HF_HOME=%~dp0hf-cache"
set "GRADIO_TEMP_DIR=%~dp0tmp"
set "TMP=%~dp0tmp"
set "TEMP=%~dp0tmp"
if not exist "%~dp0tmp" mkdir "%~dp0tmp"
echo Starting Voice Studio... browser will open at http://127.0.0.1:7860
start "" http://127.0.0.1:7860
"%~dp0venv\Scripts\python.exe" "%~dp0studio.py"

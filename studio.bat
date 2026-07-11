@echo off
rem Launch Voice Studio. Works from any folder location.
rem All output is saved to studio.log - check it if something goes wrong.
set "HF_HOME=%~dp0hf-cache"
set "GRADIO_TEMP_DIR=%~dp0tmp"
set "TMP=%~dp0tmp"
set "TEMP=%~dp0tmp"
set "PYTHONIOENCODING=utf-8"
if not exist "%~dp0tmp" mkdir "%~dp0tmp"
echo Starting Voice Studio... browser will open at http://127.0.0.1:7860
echo (This window is the server - minimize it, do not close it.)
start "" http://127.0.0.1:7860
"%~dp0venv\Scripts\python.exe" "%~dp0studio.py" > "%~dp0studio.log" 2>&1
echo.
echo ============================================================
echo Voice Studio stopped. Last lines of studio.log:
echo ============================================================
powershell -NoProfile -Command "Get-Content -Tail 15 '%~dp0studio.log'"
echo.
echo If it says the port is 'already in use', the studio is ALREADY
echo running in another window - just open http://127.0.0.1:7860
echo.
pause

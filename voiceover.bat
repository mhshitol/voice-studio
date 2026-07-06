@echo off
rem Command-line voiceover: voiceover.bat path\to\script.txt [--voice Jacob] [--vibe natural]
set "HF_HOME=%~dp0hf-cache"
"%~dp0venv\Scripts\python.exe" "%~dp0generate.py" %*

@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
 echo Once Kurulum.bat dosyasini calistirin.
 pause
 exit /b 1
)
start "DersYazi" ".venv\Scripts\pythonw.exe" app.py

@echo off
cd /d "%~dp0"
where uv >nul 2>nul
if errorlevel 1 (
 echo uv bulunamadi. https://docs.astral.sh/uv/getting-started/installation/ adresinden kurun.
 pause
 exit /b 1
)
set "UV_PYTHON_INSTALL_DIR=%~dp0.runtime"
set "UV_CACHE_DIR=%~dp0.cache"
uv venv --python 3.12 .venv
if errorlevel 1 goto fail
uv pip install --python .venv\Scripts\python.exe -r requirements-lock.txt
if errorlevel 1 goto fail
echo Kurulum tamamlandi. Baslat.bat dosyasini acabilirsiniz.
pause
exit /b 0
:fail
echo Kurulum tamamlanamadi. Yukaridaki hata mesajini kontrol edin.
pause
exit /b 1

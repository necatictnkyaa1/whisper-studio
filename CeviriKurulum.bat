@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Once Kurulum.bat dosyasini calistirin.
 pause
 exit /b 1
)
set "UV_CACHE_DIR=%~dp0.cache"
".venv\Scripts\python.exe" translation_setup.py
if errorlevel 1 goto fail
echo Ceviri kurulumu ve kisa test tamamlandi. Uygulamayi yeniden acin.
pause
exit /b 0
:fail
echo Ceviri kurulumu tamamlanamadi. Yukaridaki aciklamayi kontrol edin.
echo HTTP 403 sunucunun erisimi reddetmesidir; baglantinizin kapali oldugu anlamina gelmez.
pause
exit /b 1

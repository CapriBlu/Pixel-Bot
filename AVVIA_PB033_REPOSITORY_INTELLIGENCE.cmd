@echo off
setlocal EnableExtensions

set "START_DIR=%~dp0"
set "REPO="

rem 1) Se il launcher si trova gia nella root del progetto
if exist "%START_DIR%src\pixel_bot" if exist "%START_DIR%.git" set "REPO=%START_DIR%"

rem 2) Percorso standard del progetto
if not defined REPO if exist "C:\Users\User\OneDrive\Dokumenty\GitHub\Pixel-Bot\src\pixel_bot" set "REPO=C:\Users\User\OneDrive\Dokumenty\GitHub\Pixel-Bot\"

rem 3) Ricerca risalendo dalle cartelle del pacchetto
if not defined REPO (
  set "CUR=%START_DIR%"
  for /L %%I in (1,1,8) do call :CHECK_PARENT
)

if not defined REPO (
  echo ERRORE: repository Pixel-Bot non trovato.
  echo Posizione cercata principalmente:
  echo C:\Users\User\OneDrive\Dokumenty\GitHub\Pixel-Bot
  pause
  exit /b 1
)

cd /d "%REPO%"
set "PYTHONPATH=%REPO%src"
set "PY=%REPO%.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo ERRORE: ambiente virtuale non trovato nel repository:
  echo %PY%
  pause
  exit /b 1
)

if not exist "%REPO%src\pixel_bot\developer\run_repository_intelligence.py" (
  echo ERRORE: modulo PB-033 non installato nel repository.
  echo Reinstalla prima PB-033 oppure il relativo hotfix.
  pause
  exit /b 1
)

echo Repository: %REPO%
echo Python: %PY%
echo.
"%PY%" -m pixel_bot.developer.run_repository_intelligence "Analizzare con OpenAI e consolidare automaticamente il repository"
set "CODE=%ERRORLEVEL%"
echo.
echo === PB-033 terminato, codice: %CODE% ===
pause
exit /b %CODE%

:CHECK_PARENT
if exist "%CUR%src\pixel_bot" if exist "%CUR%.git" set "REPO=%CUR%"
for %%P in ("%CUR%..") do set "CUR=%%~fP\"
exit /b

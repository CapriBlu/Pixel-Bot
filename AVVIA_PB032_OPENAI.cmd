@echo off
setlocal EnableExtensions

set "REPO=%~dp0"
if exist "%REPO%.git" goto repo_found

set "REPO=%USERPROFILE%\OneDrive\Dokumenty\GitHub\Pixel-Bot\"
if exist "%REPO%.git" goto repo_found

set "REPO=%USERPROFILE%\OneDrive\Documents\GitHub\Pixel-Bot\"
if exist "%REPO%.git" goto repo_found

echo ERRORE: repository Pixel-Bot non trovato.
echo Avvia questo file dalla cartella principale del progetto.
pause
exit /b 1

:repo_found
cd /d "%REPO%"
set "PYTHONPATH=%REPO%src;%PYTHONPATH%"
set "PYTHON=%REPO%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo ERRORE: ambiente virtuale non trovato: %PYTHON%
  pause
  exit /b 1
)

"%PYTHON%" -c "import pixel_bot; print('Import Pixel Bot: OK')"
if errorlevel 1 (
  echo ERRORE: il modulo pixel_bot non e accessibile da %REPO%src
  pause
  exit /b 1
)

"%PYTHON%" -m pixel_bot.developer.run_state_bridge "Analizza lo stato corrente, classifica i file e indica il prossimo passo sicuro"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
  echo PB-032 OpenAI State Bridge completato correttamente.
) else (
  echo PB-032 terminato con codice %EXIT_CODE%.
)
pause
exit /b %EXIT_CODE%

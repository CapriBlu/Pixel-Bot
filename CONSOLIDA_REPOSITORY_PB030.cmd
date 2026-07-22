@echo off
setlocal
chcp 65001 >nul
set "HERE=%~dp0"
set "REPO=%CD%"

if not exist "%REPO%\pyproject.toml" (
  set "REPO=%USERPROFILE%\OneDrive\Dokumenty\GitHub\Pixel-Bot"
)

if not exist "%REPO%\launcher\Invoke-PixelBotRepositoryConsolidation.ps1" (
  echo ERRORE: PB-030 non risulta installato nel repository.
  pause
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%REPO%\launcher\Invoke-PixelBotRepositoryConsolidation.ps1" -Repo "%REPO%"
set "CODE=%ERRORLEVEL%"
echo.
echo === FINE PB-030, codice uscita: %CODE% ===
pause
exit /b %CODE%

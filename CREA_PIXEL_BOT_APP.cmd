@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "REPO=%USERPROFILE%\OneDrive\Dokumenty\GitHub\Pixel-Bot"
set "HERE=%~dp0"
set "LAUNCHER=%REPO%\launcher"

echo.
echo ==========================================
echo       CREAZIONE APP PIXEL BOT
echo ==========================================
echo.

if not exist "%REPO%" (
  echo ERRORE: repository non trovato:
  echo %REPO%
  echo.
  pause
  exit /b 1
)

if not exist "%HERE%PixelBotApp.cs" (
  echo ERRORE: PixelBotApp.cs non trovato.
  pause
  exit /b 1
)

if not exist "%HERE%PixelBot.ico" (
  echo ERRORE: PixelBot.ico non trovato.
  pause
  exit /b 1
)

if not exist "%HERE%RUN_AUTO_005_2.ps1" (
  echo ERRORE: RUN_AUTO_005_2.ps1 non trovato.
  pause
  exit /b 1
)

if not exist "%LAUNCHER%" mkdir "%LAUNCHER%"
copy /Y "%HERE%PixelBot.ico" "%LAUNCHER%\PixelBot.ico" >nul
copy /Y "%HERE%RUN_AUTO_005_2.ps1" "%LAUNCHER%\RUN_AUTO_005_2.ps1" >nul
copy /Y "%HERE%PixelBotApp.cs" "%LAUNCHER%\PixelBotApp.cs" >nul

set "CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if not exist "%CSC%" set "CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe"

if not exist "%CSC%" (
  echo ERRORE: compilatore C# di Windows non trovato.
  echo Installa .NET Framework 4.x e riprova.
  pause
  exit /b 1
)

"%CSC%" /nologo /target:winexe /out:"%LAUNCHER%\Pixel Bot.exe" /win32icon:"%LAUNCHER%\PixelBot.ico" /reference:System.dll /reference:System.Drawing.dll /reference:System.Windows.Forms.dll "%LAUNCHER%\PixelBotApp.cs"
if errorlevel 1 (
  echo.
  echo COMPILAZIONE NON RIUSCITA.
  pause
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
"$desktop=[Environment]::GetFolderPath('Desktop');" ^
"$exe='%LAUNCHER%\Pixel Bot.exe';" ^
"$icon='%LAUNCHER%\PixelBot.ico';" ^
"$lnk=Join-Path $desktop 'Pixel Bot.lnk';" ^
"$ws=New-Object -ComObject WScript.Shell;" ^
"$sc=$ws.CreateShortcut($lnk);" ^
"$sc.TargetPath=$exe;" ^
"$sc.WorkingDirectory='%REPO%';" ^
"$sc.IconLocation=$icon+',0';" ^
"$sc.Description='Apri Pixel Bot';" ^
"$sc.Save();" ^
"Write-Host ('Collegamento creato: '+$lnk) -ForegroundColor Green"

if errorlevel 1 (
  echo.
  echo APP CREATA, ma il collegamento desktop non e stato creato.
  echo Avvia manualmente: %LAUNCHER%\Pixel Bot.exe
  pause
  exit /b 1
)

echo.
echo ==========================================
echo APP CREATA CON SUCCESSO
echo ==========================================
echo.
echo Sul desktop trovi: Pixel Bot
echo La vera applicazione si trova in:
echo %LAUNCHER%\Pixel Bot.exe
echo.
pause

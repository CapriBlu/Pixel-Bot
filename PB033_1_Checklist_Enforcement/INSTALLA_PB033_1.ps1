$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Pixel Bot PB-033.1 - Checklist Enforcement"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Pixel Bot PB-033.1 - Checklist Enforcement" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$packageDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceBridge = Join-Path $packageDir "pixelbot_brain_bridge.py"
$sourceTests = Join-Path $packageDir "tests\test_checklist_enforcement.py"

$candidates = @(
    (Get-Location).Path,
    "$env:USERPROFILE\OneDrive\Dokumenty\GitHub\Pixel-Bot",
    "$env:USERPROFILE\Documents\GitHub\Pixel-Bot",
    "$env:USERPROFILE\OneDrive\Documents\GitHub\Pixel-Bot"
) | Select-Object -Unique

$repo = $null
foreach ($candidate in $candidates) {
    if ((Test-Path (Join-Path $candidate ".git")) -and
        (Test-Path (Join-Path $candidate "pixelbot_brain_bridge.py"))) {
        $repo = (Resolve-Path $candidate).Path
        break
    }
}

if (-not $repo) {
    Write-Host "ERRORE: repository Pixel-Bot non trovato." -ForegroundColor Red
    Write-Host "Avvia questo installer dalla cartella del repository oppure verifica il percorso." -ForegroundColor Yellow
    Read-Host "Premi INVIO per chiudere"
    exit 1
}

Write-Host "Repository: $repo" -ForegroundColor Green
$targetBridge = Join-Path $repo "pixelbot_brain_bridge.py"
$testsDir = Join-Path $repo "tests"
$targetTest = Join-Path $testsDir "test_checklist_enforcement.py"
$backupDir = Join-Path $repo "workspace\update-backups\PB033_1"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
New-Item -ItemType Directory -Force -Path $testsDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item $targetBridge (Join-Path $backupDir "pixelbot_brain_bridge.py.$timestamp.bak") -Force
if (Test-Path $targetTest) {
    Copy-Item $targetTest (Join-Path $backupDir "test_checklist_enforcement.py.$timestamp.bak") -Force
}

Copy-Item $sourceBridge $targetBridge -Force
Copy-Item $sourceTests $targetTest -Force
Write-Host "File installati e backup creato." -ForegroundColor Green

$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$env:PYTHONPATH = Join-Path $repo "src"
$env:PYTHONDONTWRITEBYTECODE = "1"

Write-Host ""
Write-Host "1/3 - Controllo sintassi..." -ForegroundColor Cyan
& $python -m py_compile $targetBridge
if ($LASTEXITCODE -ne 0) { throw "Controllo sintassi fallito." }

Write-Host "2/3 - Test dedicati PB-033.1..." -ForegroundColor Cyan
Push-Location $repo
try {
    & $python -m pytest -q -p no:cacheprovider tests/test_checklist_enforcement.py
    if ($LASTEXITCODE -ne 0) { throw "Test dedicati falliti." }

    Write-Host "3/3 - Suite completa..." -ForegroundColor Cyan
    & $python -m pytest -q -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) { throw "Suite completa fallita." }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "PB-033.1 installato e verificato correttamente." -ForegroundColor Green
Write-Host "Ora Pixel Bot deve eseguire ogni punto numerato, associare evidenze reali" -ForegroundColor Green
Write-Host "e non puo dichiarare completata una checklist incompleta." -ForegroundColor Green
Write-Host ""
Read-Host "Premi INVIO per chiudere"

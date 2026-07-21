param([string]$Repo = "")
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Repo)) {
    $Repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
} else {
    $Repo = (Resolve-Path -LiteralPath $Repo.Trim('"')).Path
}

Set-Location -LiteralPath $Repo
Write-Host "PB-055 AUTO-EVOLUZIONE CONTROLLATA" -ForegroundColor Red
Write-Host "Repository: $Repo"
Write-Host "Limite sessione: 1 task, nessun push automatico"

$python = Join-Path $Repo ".venv\Scripts\python.exe"
$developer = Join-Path $Repo ".venv\Scripts\pixelbot-developer.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Python virtualenv non trovato: $python" }
if (-not (Test-Path -LiteralPath $developer)) { throw "Developer Agent non trovato: $developer" }

$dirty = @(git status --porcelain)
if ($LASTEXITCODE -ne 0) { throw "Impossibile leggere lo stato Git." }
if ($dirty.Count -gt 0) {
    Write-Host ($dirty -join [Environment]::NewLine) -ForegroundColor Yellow
    throw "Repository non pulito. Eseguire commit/stash prima dell'auto-evoluzione."
}

Write-Host "`n[1/4] Test di base..." -ForegroundColor Cyan
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Test di base falliti." }

$audit = Join-Path $Repo "src\pixel_bot\developer\architecture_audit.py"
if (Test-Path -LiteralPath $audit) {
    Write-Host "`n[2/4] Audit architetturale..." -ForegroundColor Cyan
    & $python $audit $Repo
    if ($LASTEXITCODE -ne 0) { throw "Audit architetturale fallito." }
} else {
    Write-Host "`n[2/4] Audit PB-054 non disponibile: passaggio saltato." -ForegroundColor Yellow
}

$gate = Join-Path $Repo "launcher\RUN_PB031_AUTO_ADVANCE.ps1"
if (Test-Path -LiteralPath $gate) {
    Write-Host "`n[3/4] Verifica gate di avanzamento..." -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $gate -RepositoryPath $Repo
    if ($LASTEXITCODE -ne 0) { throw "Gate di avanzamento non superato." }
} else {
    Write-Host "`n[3/4] Gate PB-031 non disponibile: passaggio saltato." -ForegroundColor Yellow
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$report = Join-Path $Repo "workspace\auto-evolution\session-$stamp.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $report) | Out-Null

Write-Host "`n[4/4] Esecuzione di una task autonoma..." -ForegroundColor Cyan
& $developer `
    --run-queue `
    --repo $Repo `
    --ai `
    --apply `
    --commit `
    --max-tasks 1 `
    --max-attempts 1 `
    --queue-report $report
$agentCode = $LASTEXITCODE
if ($agentCode -ne 0) { throw "Auto-evoluzione terminata con codice $agentCode." }

Write-Host "`nVerifica finale..." -ForegroundColor Cyan
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "I test finali sono falliti." }

Write-Host "`nAUTO-EVOLUZIONE COMPLETATA" -ForegroundColor Green
Write-Host "Report: $report"
Write-Host "Controlla il commit con: git log -1 --oneline"
Write-Host "Il push resta manuale: git push"
exit 0

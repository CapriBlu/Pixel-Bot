param([string]$Repo = "")
$ErrorActionPreference = "Stop"

function Resolve-PixelBotRepository {
    param([string]$Requested)

    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($Requested)) { $candidates += $Requested }
    $candidates += @(
        "C:\Dev\Pixel-Bot",
        (Split-Path -Parent $PSScriptRoot)
    )

    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        $gitDir = Join-Path $candidate ".git"
        $project = Join-Path $candidate "pyproject.toml"
        if ((Test-Path -LiteralPath $gitDir) -and (Test-Path -LiteralPath $project)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    throw "Repository Pixel-Bot non trovato. Percorso atteso: C:\Dev\Pixel-Bot"
}

$Repo = Resolve-PixelBotRepository -Requested $Repo
Set-Location -LiteralPath $Repo

$python = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente virtuale non trovato: $python"
}

$env:PYTHONPATH = Join-Path $Repo "src"

Write-Host "PIXEL BOT - AVVIO SICURO" -ForegroundColor Cyan
Write-Host "Repository: $Repo"
Write-Host "Python: $python"

$branch = (& git -C $Repo branch --show-current).Trim()
if ($LASTEXITCODE -ne 0) { throw "Impossibile leggere il branch Git." }
Write-Host "Branch: $branch"

Write-Host "`n[1/2] Verifica import del progetto..." -ForegroundColor Cyan
& $python -c "import pixel_bot; print('Import pixel_bot: OK')"
if ($LASTEXITCODE -ne 0) { throw "Import del pacchetto pixel_bot fallito." }

Write-Host "`n[2/2] Verifica rapida del Developer Agent..." -ForegroundColor Cyan
# Non usare '--help | Select-Object': la chiusura anticipata della pipeline puo
# provocare BrokenPipe nel processo Python e un falso codice di uscita 1.
& $python -c "from pixel_bot.developer import cli; assert callable(cli.main); print('Developer Agent: OK')"
if ($LASTEXITCODE -ne 0) { throw "Developer Agent non disponibile." }

$dirty = @(& git -C $Repo status --porcelain)
Write-Host ""
if ($dirty.Count -gt 0) {
    Write-Host "Pixel Bot avviato. Repository con modifiche locali ($($dirty.Count))." -ForegroundColor Yellow
    Write-Host "Le modifiche non vengono toccate dal pulsante Avvia Pixel Bot."
} else {
    Write-Host "Pixel Bot avviato e pronto. Repository pulito." -ForegroundColor Green
}

Write-Host "Il pulsante Avvia Pixel Bot esegue soltanto il controllo di avvio sicuro."
exit 0

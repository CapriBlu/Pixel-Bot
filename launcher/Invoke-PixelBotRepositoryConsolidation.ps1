param(
    [string]$Repo = "$HOME\OneDrive\Dokumenty\GitHub\Pixel-Bot",
    [switch]$AnalyzeOnly
)

$ErrorActionPreference = "Stop"
$Repo = (Get-Item -LiteralPath $Repo).FullName
$Python = Join-Path $Repo ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Ambiente virtuale non trovato: $Python"
}

$Arguments = @("-m", "pixel_bot.repository_consolidation", "--repo", $Repo)
if (-not $AnalyzeOnly) {
    $Arguments += "--apply-safe"
}

& $Python @Arguments
$Code = $LASTEXITCODE
if ($Code -ne 0) {
    Write-Host "PB-030 terminato con errore tecnico $Code." -ForegroundColor Red
    exit $Code
}

Write-Host ""
Write-Host "PB-030 completato. Nessun commit o push e stato eseguito." -ForegroundColor Green
exit 0

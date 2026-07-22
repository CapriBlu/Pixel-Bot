param([string]$RepositoryPath = "")
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepositoryPath)) {
    $RepositoryPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
} else {
    $RepositoryPath = (Resolve-Path -LiteralPath $RepositoryPath.Trim('"')).Path
}

$venvPython = Join-Path $RepositoryPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Ambiente virtuale non trovato: $venvPython"
}

$module = Join-Path $RepositoryPath "src\pixel_bot\developer\auto_advance_gate.py"
& $venvPython $module $RepositoryPath
$code = $LASTEXITCODE
Write-Host "=== PB-031 completato, codice: $code ==="
exit $code

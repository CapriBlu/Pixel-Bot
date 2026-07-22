param([string]$Repo = "$HOME\OneDrive\Dokumenty\GitHub\Pixel-Bot")
$ErrorActionPreference = "Stop"
Set-Location $Repo
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

$python = Join-Path $Repo ".venv\Scripts\python.exe"
$pixelbot = Join-Path $Repo ".venv\Scripts\pixelbot-developer.exe"

if (-not (Test-Path $python)) { throw "Ambiente virtuale non trovato" }
if (-not (Test-Path $pixelbot)) { throw "pixelbot-developer non trovato" }

$dirty = git status --short
if ($dirty) {
  Write-Host $dirty
  Write-Warning "Repository non pulito: stato ARANCIONE. I test proseguono."
}

& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Test di base falliti. Test annullato." }

$taskPath = Join-Path $Repo "tasks\AUTO-005-2-failure-registry-initialization.json"
$task = @'
{
  "task_id": "AUTO-005.2",
  "title": "Correggere inizializzazione FailureRegistry",
  "objective": "Correggere esclusivamente l'inizializzazione della classe FailureRegistry quando usa dataclass con slots, assicurando che il percorso del registro sia dichiarato e inizializzato correttamente senza modificare il Developer Agent o altre componenti.",
  "acceptance_criteria": [
    "FailureRegistry può essere istanziato senza AttributeError.",
    "Il percorso workspace/test-failure-registry viene calcolato correttamente.",
    "I test specifici del FailureRegistry passano.",
    "Tutta la suite pytest passa senza warning.",
    "La modifica coinvolge al massimo due file.",
    "Nessuna modifica viene apportata ad agent.py, models.py o repository.py."
  ],
  "allowed_paths": [
    "src/pixel_bot/developer/failure_registry.py",
    "tests/test_failure_registry.py"
  ],
  "test_command": ["python", "-m", "pytest", "-q"],
  "metadata": {
    "mode": "autonomous-magi-supervised",
    "priority": 1,
    "milestone": "failure-registry-foundation",
    "max_files": 2,
    "requires_backward_compatibility": true,
    "requires_rollback": true,
    "next_proposal_auto_apply": false
  }
}
'@

[System.IO.File]::WriteAllText($taskPath, $task, [System.Text.UTF8Encoding]::new($false))
& $python -c "import json; json.load(open(r'$taskPath', encoding='utf-8')); print('AUTO-005.2 valido')"

git add -- "tasks/AUTO-005-2-failure-registry-initialization.json"
git commit -m "AUTO-005.2 add FailureRegistry initialization task"

& $pixelbot "tasks/AUTO-005-2-failure-registry-initialization.json" --ai --apply --commit --report "workspace/AUTO-005-2-report.json"
$agentExit = $LASTEXITCODE

& $python -m pytest -q
$pytestExit = $LASTEXITCODE

$backups = @(Get-ChildItem $Repo -Recurse -Filter "*.pixelbot.bak" -ErrorAction SilentlyContinue)
$gitFinal = git status --short

Write-Host "Agent exit code: $agentExit"
Write-Host "Pytest exit code: $pytestExit"
Write-Host "Backup residui: $($backups.Count)"
Write-Host "Git status:"
$gitFinal

if (Test-Path (Join-Path $Repo "workspace\AUTO-005-2-report.json")) {
  Get-Content (Join-Path $Repo "workspace\AUTO-005-2-report.json") -Encoding UTF8
}

# PB-029 DIAGNOSTIC SUMMARY
$DiagnosticScript = Join-Path $Repo "launcher\Write-PixelBotDiagnosticSummary.ps1"
$AgentReport = Join-Path $Repo "workspace\AUTO-005-2-report.json"
if (-not (Test-Path -LiteralPath $DiagnosticScript)) {
  Write-Host "ERRORE: modulo diagnostico PB-029 non trovato: $DiagnosticScript" -ForegroundColor Red
  exit 1
}

& $DiagnosticScript `
  -Repo $Repo `
  -AgentExitCode $agentExit `
  -PytestExitCode $pytestExit `
  -ReportPath $AgentReport `
  -OperationName "AUTO-005.2 FailureRegistry"
exit $LASTEXITCODE


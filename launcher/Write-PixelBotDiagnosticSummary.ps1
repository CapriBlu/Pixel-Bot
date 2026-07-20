param(
    [Parameter(Mandatory = $true)][string]$Repo,
    [int]$AgentExitCode = 0,
    [int]$PytestExitCode = 0,
    [string]$ReportPath = "",
    [string]$OperationName = "Aggiornamento Pixel Bot"
)

$ErrorActionPreference = "Continue"
$Repo = (Get-Item -LiteralPath $Repo).FullName
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$OutputRoot = Join-Path $Repo "workspace\update-diagnostics"
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

$Issues = [System.Collections.Generic.List[object]]::new()
function Add-Issue {
    param([string]$Severity, [string]$Category, [string]$Origin, [string]$Description, [string]$Consequence, [string]$Action)
    $Issues.Add([ordered]@{
        severity = $Severity
        category = $Category
        origin = $Origin
        description = $Description
        consequence = $Consequence
        recommended_action = $Action
    })
}

$GitAvailable = $false
$GitStatus = @()
$CurrentCommit = $null
try {
    Push-Location -LiteralPath $Repo
    git rev-parse --is-inside-work-tree *> $null
    if ($LASTEXITCODE -eq 0) {
        $GitAvailable = $true
        $GitStatus = @(git status --porcelain=v1)
        $CurrentCommit = (git rev-parse HEAD).Trim()
    }
}
catch {
    Add-Issue "warning" "GIT" "git" "Git non disponibile o repository non riconosciuto." "Non e possibile verificare la base dell'aggiornamento." "Verificare Git e il percorso del repository."
}
finally {
    Pop-Location
}

$Backups = @(Get-ChildItem -LiteralPath $Repo -Recurse -Filter "*.pixelbot.bak" -File -ErrorAction SilentlyContinue)
$ReportedCommit = $null
$ReportLoaded = $false
if (-not [string]::IsNullOrWhiteSpace($ReportPath) -and (Test-Path -LiteralPath $ReportPath)) {
    try {
        $Report = Get-Content -LiteralPath $ReportPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $ReportLoaded = $true
        if ($null -ne $Report.git -and $null -ne $Report.git.commit_sha) {
            $ReportedCommit = [string]$Report.git.commit_sha
        }
    }
    catch {
        Add-Issue "warning" "REPORT" "report parser" "Il report JSON non e leggibile." "Il riepilogo potrebbe non contenere tutti i dettagli." "Rigenerare il report dell'operazione."
    }
}

if ($AgentExitCode -ne 0) {
    Add-Issue "error" "AGENT" "developer agent" "L'agente e terminato con codice $AgentExitCode." "La modifica potrebbe essere incompleta o non applicata." "Aprire il report dell'agente, correggere l'errore e ripetere l'operazione."
}
if ($PytestExitCode -ne 0) {
    Add-Issue "error" "TEST" "pytest" "La suite di test e terminata con codice $PytestExitCode." "La versione non e considerata sicura." "Esaminare i test falliti e correggerli prima di continuare."
}
if ($Backups.Count -gt 0) {
    Add-Issue "warning" "CLEANUP" "backup manager" "Sono presenti $($Backups.Count) backup .pixelbot.bak nel repository." "Il repository resta ARANCIONE, ma l'operazione non e fallita." "Verificare i backup e spostarli in workspace\update-backups."
}
if ($GitAvailable -and $GitStatus.Count -gt 0) {
    Add-Issue "warning" "GIT" "working tree" "Il repository contiene $($GitStatus.Count) modifiche o file non classificati." "Non e prudente stratificare un nuovo aggiornamento." "Classificare, consolidare o ignorare i file e ripetere la verifica."
}
if ($ReportedCommit -and $CurrentCommit -and $ReportedCommit -ne $CurrentCommit) {
    Add-Issue "warning" "REPORT" "commit verification" "Il commit del report ($ReportedCommit) non coincide con HEAD ($CurrentCommit)." "Il report non rappresenta lo stato finale del repository." "Rigenerare il report dopo il commit finale."
}

$HasErrors = @($Issues | Where-Object { $_.severity -eq "error" }).Count -gt 0
$HasWarnings = @($Issues | Where-Object { $_.severity -eq "warning" }).Count -gt 0
if ($HasErrors) { $Status = "red"; $ExitCode = 1 }
elseif ($HasWarnings) { $Status = "orange"; $ExitCode = 0 }
else { $Status = "green"; $ExitCode = 0 }

$StatusLabel = switch ($Status) { "green" { "VERDE" } "orange" { "ARANCIONE" } default { "ROSSO" } }
$Summary = [ordered]@{
    schema_version = 1
    operation = $OperationName
    timestamp = (Get-Date).ToString("o")
    status = $Status
    exit_code = $ExitCode
    agent_exit_code = $AgentExitCode
    pytest_exit_code = $PytestExitCode
    tests_passed = ($PytestExitCode -eq 0)
    git_available = $GitAvailable
    current_commit = $CurrentCommit
    reported_commit = $ReportedCommit
    report_loaded = $ReportLoaded
    backup_count = $Backups.Count
    backups = @($Backups | ForEach-Object { $_.FullName.Substring($Repo.Length).TrimStart("\") })
    git_status = $GitStatus
    issues = $Issues
    ready_for_next_update = ($Status -eq "green")
}

$JsonPath = Join-Path $OutputRoot "diagnostic-$Timestamp.json"
$TextPath = Join-Path $OutputRoot "diagnostic-$Timestamp.txt"
$Summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $JsonPath -Encoding UTF8

$Lines = [System.Collections.Generic.List[string]]::new()
$Lines.Add("RISULTATO AGGIORNAMENTO")
$Lines.Add("=======================")
$Lines.Add("Stato generale: $StatusLabel")
$Lines.Add("Codice uscita: $ExitCode")
$Lines.Add("Agente: $AgentExitCode")
$Lines.Add("Pytest: $PytestExitCode")
$Lines.Add("Backup residui: $($Backups.Count)")
$Lines.Add("Commit corrente: $CurrentCommit")
if ($ReportedCommit) { $Lines.Add("Commit nel report: $ReportedCommit") }
$Lines.Add("")
if ($Issues.Count -eq 0) {
    $Lines.Add("Nessun problema rilevato. Il sistema e pronto per il prossimo aggiornamento.")
}
else {
    $Lines.Add("PROBLEMI RILEVATI")
    $Lines.Add("-----------------")
    $Index = 1
    foreach ($Issue in $Issues) {
        $Lines.Add("$Index. [$($Issue.severity.ToUpper())] $($Issue.category)")
        $Lines.Add("   Origine: $($Issue.origin)")
        $Lines.Add("   Descrizione: $($Issue.description)")
        $Lines.Add("   Conseguenza: $($Issue.consequence)")
        $Lines.Add("   Azione consigliata: $($Issue.recommended_action)")
        $Lines.Add("")
        $Index++
    }
}
$Lines.Add("Report JSON: $JsonPath")
$Lines.Add("Report leggibile: $TextPath")
$Lines | Set-Content -LiteralPath $TextPath -Encoding UTF8

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "RISULTATO AGGIORNAMENTO: $StatusLabel" -ForegroundColor $(if ($Status -eq "green") { "Green" } elseif ($Status -eq "orange") { "Yellow" } else { "Red" })
Write-Host "============================================================" -ForegroundColor Cyan
$Lines | ForEach-Object { Write-Host $_ }

exit $ExitCode

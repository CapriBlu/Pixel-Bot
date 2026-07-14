# Aggiornamento autonomo controllato

Pixel Bot può ora usare il Developer Agent per generare modifiche tramite il backend AI già condiviso con gli altri servizi.

## Flusso sicuro

1. Carica un task JSON.
2. Analizza il repository e seleziona i file rilevanti.
3. Chiede al backend AI modifiche complete nel formato `file_changes_v1`.
4. In anteprima non modifica alcun file.
5. Applica le modifiche solo con `--apply`.
6. Esegue i test configurati dal task.
7. In caso di errore ripristina i file originali.
8. Commit, push e Pull Request draft richiedono flag espliciti.
9. Il merge sulla branch principale resta manuale.

## Anteprima con AI

```powershell
$env:PIXEL_BOT_AI_ENDPOINT = "https://backend.example/api/pixel/developer"
$env:PIXEL_BOT_AI_TOKEN = "..."
python -m pixel_bot.developer.cli tasks/PB-006-autonomous-update.json --ai
```

## Applicazione e test

```powershell
python -m pixel_bot.developer.cli tasks/PB-006-autonomous-update.json --ai --apply
```

## Commit e Pull Request draft

```powershell
python -m pixel_bot.developer.cli tasks/PB-006-autonomous-update.json --ai --apply --open-pr
```

## Simulazione senza consumo API

```powershell
$env:PIXEL_BOT_DRY_RUN = "1"
python -m pixel_bot.developer.cli tasks/PB-006-autonomous-update.json `
  --ai `
  --simulation-changes tasks/example-file-changes.json
```

## Sessione continua della task queue (PB-009)

La CLI può eseguire una sessione autonoma limitata con `--run-queue`. Per sicurezza la sessione:

- esegue al massimo `--max-tasks` task (default 5);
- si arresta al primo errore, salvo `--continue-on-failure`;
- persiste lo stato di ogni task;
- crea report individuali in `workspace/task-reports/`;
- crea un report cumulativo in `workspace/queue-session-report.json`;
- mantiene push, PR e merge dietro flag espliciti.

```powershell
python -m pixel_bot.developer.cli `
  --run-queue `
  --repo . `
  --ai `
  --apply `
  --commit `
  --max-tasks 3
```

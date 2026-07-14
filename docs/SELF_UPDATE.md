# Primo aggiornamento autonomo controllato

PB-007 verifica l'intero ciclo del Developer Agent senza consumare credito API.
La generazione e simulata, mentre applicazione, test, branch e commit sono reali.

## Esecuzione locale

Dalla root del repository, con l'ambiente virtuale attivo:

```powershell
$env:PIXEL_BOT_DRY_RUN = "1"
python -m pixel_bot.developer.cli `
  tasks/PB-007-self-update-demo.json `
  --ai `
  --simulation-changes tasks/PB-007-self-update-demo.changes.json `
  --apply `
  --commit `
  --report workspace/PB-007-report.json
```

Il comando deve:

- creare `docs/SELF_UPDATE_DEMO.md`;
- eseguire la suite configurata nel task;
- creare la branch `pixelbot/pb-007-primo-aggiornamento-autonomo-controllato`;
- creare un commit se i test passano;
- produrre `workspace/PB-007-report.json`.

Per pubblicare la branch aggiungere `--push`. Per aprire anche una Pull Request
draft aggiungere `--open-pr`. Queste operazioni richiedono configurazione Git e
GitHub CLI e non sono mai eseguite implicitamente.

## Sicurezza

Il task autorizza soltanto il percorso `docs`. Se i test falliscono, il file
creato viene rimosso o ripristinato automaticamente. Il merge su `main` resta
manuale.

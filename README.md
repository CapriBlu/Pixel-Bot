# Pixel Bot

Pixel Bot è un **Desktop AI Agent intelligente** progettato per osservare lo schermo, comprendere un obiettivo espresso in linguaggio naturale, pianificare il passo successivo, eseguire azioni sul computer, verificare il risultato e continuare fino al completamento del lavoro.

Il progetto non nasce come semplice macro, script di automazione o assistente che esegue comandi fissi. L'obiettivo è costruire un agente capace di lavorare attraverso un **loop autonomo controllato**, con memoria operativa, verifica continua, correzione degli errori e possibilità di migliorare progressivamente il proprio codice tramite un developer loop sicuro.

## Visione del progetto

Pixel Bot dovrà diventare un assistente desktop capace di:

- vedere e interpretare ciò che accade sullo schermo;
- ricevere obiettivi complessi in linguaggio naturale;
- decidere una singola azione utile alla volta;
- usare mouse, tastiera, applicazioni e finestre autorizzate;
- verificare visivamente gli effetti di ogni azione;
- riconoscere errori, schermate inattese e cambiamenti dell'interfaccia;
- correggere il piano senza ripetere meccanicamente gli stessi passaggi;
- mantenere una cronologia delle decisioni e dei risultati;
- interrompersi quando il compito è completato, bloccato o non sicuro;
- proporre e sviluppare miglioramenti al proprio codice attraverso un processo verificabile.

## Il loop principale

Il comportamento centrale di Pixel Bot è basato sul seguente ciclo:

```text
Obiettivo dell'utente
        ↓
Acquisizione dello schermo
        ↓
Analisi AI del contesto
        ↓
Decisione della prossima azione
        ↓
Validazione di sicurezza
        ↓
Conferma umana, quando richiesta
        ↓
Esecuzione dell'azione
        ↓
Nuovo screenshot
        ↓
Verifica del risultato
        ↓
Completamento oppure nuovo ciclo
```

In forma semplificata:

```python
while not completed and step < max_steps:
    screenshot = capture_screen()
    decision = ai_client.analyze(
        goal=goal,
        screenshot=screenshot,
        history=history,
    )

    if decision.completed:
        break

    action = decision.to_action()
    validate_action(action)
    request_confirmation_if_needed(action)
    result = execute_action(action)
    history.append(decision, result)
```

L'agente deve produrre **una sola azione per ciclo**. Questa scelta rende il comportamento osservabile, verificabile e più semplice da interrompere o correggere.

## Decisione strutturata dell'AI

L'AI non deve restituire testo libero da eseguire direttamente. Ogni decisione deve rispettare un formato strutturato simile al seguente:

```json
{
  "observation": "È aperto il desktop di Windows.",
  "reasoning_summary": "Per raggiungere l'obiettivo bisogna aprire Blocco note.",
  "action": {
    "name": "open_app",
    "parameters": {
      "app": "notepad"
    }
  },
  "completed": false
}
```

Quando il lavoro è concluso:

```json
{
  "observation": "Il contenuto richiesto è presente nella finestra corretta.",
  "reasoning_summary": "L'obiettivo è stato completato.",
  "action": null,
  "completed": true
}
```

Le risposte vengono convertite in oggetti `AgentDecision`, validate e trasformate in azioni solo dopo avere superato i controlli di sicurezza.

## Desktop AI Agent

Pixel Bot sarà composto da più livelli specializzati.

### Visione

Responsabile di:

- acquisizione dello schermo;
- gestione di uno o più monitor;
- preparazione delle immagini per il modello AI;
- individuazione di finestre, pulsanti, campi e messaggi;
- confronto tra lo stato precedente e quello successivo.

### Comprensione e pianificazione

Responsabile di:

- interpretare l'obiettivo dell'utente;
- analizzare screenshot e cronologia;
- scegliere il passo successivo;
- capire quando il lavoro è terminato;
- riconoscere blocchi, errori e situazioni ambigue.

### Esecuzione

Responsabile di:

- movimento e clic del mouse;
- scrittura e pressione dei tasti;
- apertura di applicazioni autorizzate;
- gestione e messa a fuoco delle finestre;
- attese controllate;
- acquisizione di nuovi screenshot.

### Sicurezza

Responsabile di:

- allowlist delle azioni disponibili;
- allowlist delle applicazioni apribili;
- validazione dei parametri;
- limiti sul numero di passaggi;
- timeout;
- stop manuale immediato;
- richiesta di conferma per operazioni sensibili;
- registrazione completa delle azioni;
- blocco di comandi non autorizzati.

### Memoria operativa

Responsabile di conservare:

- obiettivo corrente;
- screenshot precedenti;
- decisioni dell'AI;
- azioni eseguite;
- risultati ottenuti;
- errori incontrati;
- tentativi già effettuati;
- stato corrente del task.

La memoria serve a evitare loop ripetitivi e permette all'agente di correggere la propria strategia.

## Developer Loop

Pixel Bot dovrà anche possedere un **developer loop**: un processo con cui può analizzare il proprio progetto, individuare limiti, proporre modifiche, scrivere codice, eseguire test e preparare aggiornamenti.

Il developer loop previsto è:

```text
Analisi del repository
        ↓
Individuazione di un limite o di un obiettivo tecnico
        ↓
Proposta di modifica
        ↓
Creazione di una branch dedicata
        ↓
Scrittura o aggiornamento del codice
        ↓
Esecuzione di test e controlli
        ↓
Analisi dei risultati
        ↓
Correzione degli errori
        ↓
Pull request per revisione umana
```

### Auto-sviluppo controllato

Per "auto-svilupparsi" si intende che Pixel Bot potrà:

- leggere il proprio codice e la documentazione;
- individuare funzionalità mancanti o problemi tecnici;
- proporre una soluzione;
- modificare file esclusivamente in una branch separata;
- creare o aggiornare test;
- eseguire verifiche automatiche;
- analizzare errori di test e correggere la modifica;
- preparare una pull request;
- attendere l'approvazione umana prima dell'integrazione nel branch principale.

Pixel Bot **non deve modificare autonomamente il branch principale**, disattivare i controlli di sicurezza o distribuire codice non revisionato. L'auto-miglioramento deve restare tracciabile, reversibile e sottoposto ad approvazione.

## Architettura attuale

```text
src/pixel_bot/
├── agent/
│   ├── __init__.py
│   ├── models.py
│   ├── prompts.py
│   ├── ai_client.py       # previsto
│   └── loop.py            # previsto
├── automation/
│   ├── keyboard_controller.py
│   └── mouse_controller.py
├── core/
│   ├── command_parser.py
│   ├── execution_manager.py
│   ├── executor.py
│   ├── logger.py
│   ├── planner.py
│   ├── safety.py
│   └── task_runner.py
├── interface/
│   ├── console.py
│   └── control_center.py
└── vision/
    ├── screen_capture.py
    └── window_controller.py
```

## Funzionalità già presenti

- acquisizione dello schermo;
- controllo sicuro del mouse;
- controllo sicuro della tastiera;
- apertura di applicazioni autorizzate;
- messa a fuoco delle finestre;
- interprete di comandi testuali;
- esecuzione di task JSON;
- planner deterministico;
- Execution Manager;
- Control Center grafico;
- logging delle azioni;
- test automatici;
- workflow GitHub Actions;
- modello strutturato `AgentDecision`;
- branch dedicata al primo loop agentico.

## Roadmap

### Fase 1 — Agent Loop v0.1

- completare `AgentDecision`;
- implementare `AIClient`;
- inviare screenshot e obiettivo al modello AI;
- validare la risposta JSON;
- implementare `AgentLoop`;
- limitare il numero massimo di passaggi;
- aggiungere stop manuale;
- registrare cronologia e risultati;
- eseguire una sola azione per ciclo.

### Fase 2 — Integrazione Control Center

- campo per l'obiettivo;
- anteprima della decisione AI;
- visualizzazione dell'osservazione;
- visualizzazione dell'azione proposta;
- pulsanti Conferma, Rifiuta e Stop;
- modalità passo-passo;
- modalità automatica controllata;
- pannello della cronologia.

### Fase 3 — Verifica intelligente

- confronto tra screenshot prima e dopo;
- rilevamento delle azioni senza effetto;
- riconoscimento di finestre inattese;
- prevenzione dei loop ripetitivi;
- gestione di retry e strategie alternative;
- riconoscimento affidabile del completamento.

### Fase 4 — Memoria e task complessi

- memoria persistente dei task;
- ripresa di un lavoro interrotto;
- suddivisione degli obiettivi in sotto-obiettivi;
- gestione di task lunghi;
- report finale delle operazioni eseguite.

### Fase 5 — Developer Agent

- lettura strutturata del repository;
- analisi di issue, test e log;
- pianificazione delle modifiche;
- generazione di patch;
- esecuzione automatica dei test;
- correzione iterativa degli errori;
- creazione di branch e pull request;
- revisione umana obbligatoria prima del merge.

## Principi di sicurezza

Pixel Bot deve rispettare sempre questi principi:

1. nessuna azione fuori dalla allowlist;
2. nessun comando arbitrario di terminale nelle prime versioni;
3. nessuna gestione autonoma di password o credenziali;
4. nessuna cancellazione di file senza autorizzazione esplicita;
5. nessun acquisto, pagamento o invio definitivo senza conferma;
6. nessuna modifica diretta al branch principale nel developer loop;
7. limite massimo di passaggi per ogni task;
8. arresto manuale sempre disponibile;
9. log completo e leggibile delle decisioni;
10. comportamento conservativo in caso di dubbio.

## Stato del progetto

Pixel Bot è attualmente in fase di sviluppo iniziale avanzato. La base di automazione desktop è disponibile e il lavoro corrente è concentrato sull'implementazione del primo ciclo intelligente:

```text
Screenshot → AI → Decisione → Validazione → Esecuzione → Verifica → Ripetizione
```

Il traguardo immediato è ottenere un primo agente che possa completare semplici attività desktop in modalità passo-passo, con una decisione alla volta e supervisione umana.

## Obiettivo finale

L'obiettivo finale è realizzare un agente desktop capace di:

- lavorare su applicazioni reali;
- adattarsi alle interfacce visive;
- completare attività multi-step;
- imparare dai risultati operativi;
- migliorare progressivamente i propri strumenti;
- contribuire allo sviluppo del proprio codice;
- mantenere sempre sicurezza, controllo umano e tracciabilità.

Pixel Bot vuole diventare non soltanto un bot che usa il computer, ma una piattaforma per costruire un **assistente operativo e developer AI intelligente, verificabile e progressivamente autonomo**.

## Developer Agent v0.1

La branch di sviluppo include il primo ciclo controllato di auto-sviluppo:

```text
Task JSON -> analisi repository -> piano -> modifiche strutturate -> test -> report
```

Esempio in sola pianificazione:

```powershell
$env:PYTHONPATH = "src"
python -m pixel_bot.developer.cli tasks/PB-003-developer-agent.json
```

Esempio con modifiche già generate dal backend AI:

```powershell
$env:PYTHONPATH = "src"
python -m pixel_bot.developer.cli tasks/PB-003-developer-agent.json `
  --changes workspace/proposed-changes.json `
  --apply
```

Il file delle modifiche è una lista JSON di oggetti con `path`, `content` e `reason`.
Il Developer Agent accetta soltanto percorsi autorizzati dal task, crea backup, esegue i test e ripristina automaticamente i file quando i test falliscono. Il merge su `main` richiede sempre revisione umana.

## Git Manager controllato (PB-005)

Il Developer Agent può ora chiudere il ciclo di aggiornamento con operazioni Git sicure:

- crea automaticamente una branch `pixelbot/<task-id>-<titolo>` quando parte da `main` o da un'altra branch protetta;
- aggiunge al commit esclusivamente i file modificati dal task;
- crea il commit solo dopo test verdi;
- esegue `push` soltanto con l'opzione esplicita `--push`;
- apre una Pull Request **draft** tramite GitHub CLI soltanto con `--open-pr`;
- mantiene il merge su `main` subordinato alla revisione umana.

Esempio locale:

```powershell
python -m pixel_bot.developer.cli tasks/PB-005-git-manager.json `
  --changes workspace/file-changes.json `
  --apply --commit
```

Per pubblicare e aprire una PR draft, dopo aver configurato `gh auth login`:

```powershell
python -m pixel_bot.developer.cli tasks/PB-005-git-manager.json `
  --changes workspace/file-changes.json `
  --apply --open-pr
```

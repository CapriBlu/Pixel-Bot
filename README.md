# Pixel Bot

Pixel Bot è un assistente desktop sperimentale per Windows progettato per osservare lo schermo, interpretare obiettivi espressi in linguaggio naturale, costruire un piano di azioni e interagire con applicazioni attraverso mouse e tastiera entro regole di sicurezza verificabili.

> Stato: prototipo v0.2 in sviluppo. Il progetto non è ancora destinato all'esecuzione non supervisionata su sistemi di produzione.

## Obiettivi

- acquisire screenshot del desktop;
- interpretare comandi testuali;
- trasformare un obiettivo in un piano di azioni;
- mostrare il piano prima dell'esecuzione;
- controllare mouse, tastiera, finestre e applicazioni consentite;
- registrare azioni, risultati ed errori;
- integrare OCR e AI Vision;
- aumentare progressivamente l'autonomia mantenendo conferme, limiti e possibilità di arresto.

## Requisiti

- Windows 10 o Windows 11;
- Python 3.12 consigliato;
- Git;
- ambiente desktop grafico attivo;
- permessi per acquisizione schermo e automazione input.

## Installazione

```powershell
git clone https://github.com/CapriBlu/Pixel-Bot.git
cd Pixel-Bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se PowerShell blocca l'attivazione dell'ambiente virtuale:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Configurazione

Crea un file `.env` nella cartella principale solo quando vengono abilitate integrazioni esterne. Non inserire chiavi API nel repository.

Esempio previsto:

```env
OPENAI_API_KEY=
PIXEL_BOT_LOG_LEVEL=INFO
PIXEL_BOT_DRY_RUN=true
```

Le variabili non ancora implementate sono specifiche previste e devono essere collegate al modulo Settings prima dell'MVP.

## Avvio

### Control Center grafico

```powershell
$env:PYTHONPATH="src"
python -m pixel_bot.interface.control_center
```

### Console

```powershell
$env:PYTHONPATH="src"
python main.py
```

### Test

```powershell
$env:PYTHONPATH="src"
pytest -q
```

### Verifica sintattica

```powershell
python -m compileall -q src/pixel_bot
```

## Struttura del progetto

```text
Pixel-Bot/
├── .github/workflows/       # test automatici GitHub Actions
├── docs/                    # architettura, API, roadmap e governance
├── logs/                    # log locali, esclusi da Git
├── screenshots/             # immagini acquisite, escluse da Git
├── src/pixel_bot/
│   ├── automation/          # mouse e tastiera
│   ├── core/                # parser, planner, executor, safety, logging
│   ├── interface/           # console e Control Center Tkinter
│   ├── vision/              # acquisizione schermo e finestre
│   └── magi/                # valutazione delle decisioni evolutive
├── tests/                   # test automatici
├── main.py                  # ingresso console
├── pytest.ini               # configurazione test
├── requirements.txt         # dipendenze Python
└── README.md
```

La struttura può evolvere durante lo sprint; ogni modifica significativa deve essere riflessa qui e in `docs/ARCHITECTURE.md`.

## Tecnologie utilizzate

- Python 3.12;
- Tkinter / ttk per il Control Center;
- PyAutoGUI per mouse e tastiera;
- MSS e Pillow per acquisizione e gestione immagini;
- PyGetWindow per interazione con finestre;
- python-dotenv per configurazione locale;
- pytest per test automatici;
- GitHub Actions per CI su Windows.

## Flusso operativo attuale

1. L'utente inserisce un obiettivo.
2. Il parser traduce il testo in azioni note.
3. Il Planner crea un piano ordinato.
4. Il livello Safety valida azioni e parametri.
5. Il Control Center mostra il piano e richiede conferma.
6. L'Execution Manager esegue i passaggi.
7. Executor e controller interagiscono con il desktop.
8. Log, eventi, risultati ed errori vengono restituiti all'interfaccia.

OCR e AI Vision sono estensioni previste: dovranno trasformare screenshot e regioni dello schermo in osservazioni strutturate utilizzabili dal Planner.

## Sicurezza

- esecuzione supervisionata come impostazione predefinita;
- anteprima del piano prima dell'avvio;
- applicazioni e azioni consentite tramite allowlist;
- validazione dei parametri;
- pulsante o comando di arresto;
- log delle operazioni;
- modalità dry-run prevista;
- nessuna chiave API nel codice o nei commit.

## MVP definito

L'MVP è completato quando un nuovo sviluppatore può installare Pixel Bot su Windows e dimostrare questo scenario:

1. avviare il Control Center;
2. acquisire e visualizzare uno screenshot;
3. inserire un comando supportato;
4. vedere il piano prima dell'esecuzione;
5. confermare o annullare;
6. eseguire un'azione controllata di mouse o tastiera in un'app consentita;
7. interrompere il piano in corso;
8. consultare log ed eventuali errori;
9. eseguire la suite di test con esito positivo.

L'MVP non include autonomia completa, navigazione universale dell'interfaccia o modifica autonoma del sistema senza supervisione.

## Roadmap sintetica

### Sprint 1 — Documentazione e consegna MVP

- README completo;
- architettura e flussi documentati;
- contratto API previsto;
- backlog GitHub granulare;
- criteri di accettazione MVP;
- verifica installazione pulita su Windows.

### Sprint 2 — Visione locale

- screenshot per monitor e regione;
- OCR con output strutturato;
- rilevamento finestre ed elementi base;
- test con immagini fixture.

### Sprint 3 — AI Vision

- provider configurabile;
- redazione dei dati sensibili;
- invio controllato delle immagini;
- schema JSON delle osservazioni;
- gestione timeout, costi e fallback.

### Sprint 4 — Affidabilità e sicurezza

- Settings persistenti;
- dry-run completo;
- retry limitati;
- codici errore;
- log strutturati e rotazione;
- test end-to-end.

### Sprint 5 — Autonomia supervisionata

- ciclo osserva-pianifica-agisci-verifica;
- checkpoint umani;
- memoria del task;
- rollback e criteri di arresto;
- governance MAGI integrata.

Dettagli in `docs/ROADMAP.md`.

## Documentazione

- [Architettura](docs/ARCHITECTURE.md)
- [API previste](docs/API.md)
- [Roadmap e sprint](docs/ROADMAP.md)
- [Definizione MVP](docs/MVP.md)
- [Governance MAGI](docs/MAGI.md)

## Contribuire

1. aprire o selezionare una issue;
2. creare un branch dedicato;
3. implementare una modifica piccola e verificabile;
4. aggiungere o aggiornare i test;
5. aggiornare la documentazione interessata;
6. aprire una pull request descrivendo comportamento, rischi e verifica eseguita.

Formato consigliato dei commit:

```text
PB-### descrizione breve
```

## Limitazioni note

- supporto principale Windows;
- insieme di comandi ancora limitato;
- OCR e AI Vision non ancora consolidati;
- automazione grafica sensibile a risoluzione, zoom e disposizione delle finestre;
- necessaria supervisione umana durante lo sviluppo.

## Licenza

La licenza non è ancora definita. Prima di distribuire o accettare contributi esterni deve essere aggiunto un file `LICENSE`.
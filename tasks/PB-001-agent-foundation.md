# PB-001 — Consolidare Workspace e Memory

## Stato

`READY`

## Milestone

0.3 — Agent Foundation

## Obiettivo

Fornire a Pixel Bot una struttura persistente e verificabile per conservare sessioni, screenshot, decisioni, risultati ed errori.

## Requisiti funzionali

1. Creare automaticamente le directory del workspace.
2. Generare un identificatore univoco per ogni sessione.
3. Salvare una cronologia JSONL append-only.
4. Salvare un riepilogo JSON della sessione.
5. Conservare riferimenti agli screenshot senza duplicare dati inutilmente.
6. Restituire al modello solo gli ultimi eventi configurabili.
7. Non salvare chiavi API, password o contenuti esplicitamente marcati come sensibili.
8. Consentire una modalità temporanea per i test.

## API minima desiderata

```python
workspace = Workspace(root="workspace")
session = workspace.create_session(goal="Apri Blocco note")

memory = SessionMemory(session)
memory.append("decision", payload)
memory.append("action_result", payload)
recent = memory.recent(limit=10)
memory.complete(status="completed")
```

## Percorsi previsti

```text
workspace/
  sessions/
    <session-id>/
      screenshots/
      history.jsonl
      summary.json
      logs/
      plans/
      patches/
```

## Test richiesti

- creazione delle directory;
- session ID univoci;
- append e lettura della cronologia;
- limite degli eventi recenti;
- riepilogo finale;
- serializzazione corretta;
- nessuna dipendenza da rete o GUI.

## Criteri di accettazione

- tutti i test passano;
- il modulo è indipendente dall'interfaccia grafica;
- l'Agent Loop può ricevere Memory e Workspace tramite dependency injection;
- il comportamento precedente del bot non viene rotto;
- la documentazione viene aggiornata.

## Vincoli di sicurezza

- non cancellare sessioni automaticamente;
- non scrivere fuori dalla root configurata;
- rifiutare percorsi che tentano directory traversal;
- non includere segreti nei log.

## Prossimo task dopo il completamento

PB-002 — Integrare AI Client, budget e modalità simulazione nell'Agent Loop.

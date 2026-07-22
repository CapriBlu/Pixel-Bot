# Pixel Bot — Architettura

## Panoramica

Pixel Bot è organizzato come una piattaforma ad agenti. Il Desktop Agent opera sullo schermo; il Developer Agent opera sul repository. I due agenti condividono memoria, workspace, AI Client, sicurezza ed eventi.

```text
User Goal
   |
Goal Manager
   |
Planner
   |
Agent Runtime
   |----------------------|
Desktop Agent       Developer Agent
   |                      |
Vision + Executor   Repository + Tests + Git
   |----------------------|
Workspace + Memory + Events + Safety + AI Client
```

## Componenti principali

### AI Client

Adattatore verso il backend AI già utilizzato dall'applicazione Fatture. Non conserva chiavi OpenAI nel client desktop. Invia screenshot, goal, cronologia e schema di risposta; riceve JSON validato.

### Workspace

Directory persistente usata per:

- screenshot
- history
- memory
- plans
- patches
- logs
- cache
- tasks

Il Workspace non deve contenere segreti e deve supportare sessioni separate.

### Memory

Conserva decisioni, azioni, risultati, errori e tentativi. Deve offrire una vista compatta da inviare al modello e una cronologia completa per audit.

### Goal Manager

Normalizza l'obiettivo, assegna un identificatore alla sessione, applica limiti e definisce il criterio di successo.

### Planner

Trasforma un goal in step verificabili. Ogni step deve avere stato, azione prevista, criterio di successo e strategia di recupero.

### Desktop Agent

Esegue il ciclo:

```text
screenshot -> decisione AI -> validazione -> conferma -> esecuzione -> verifica
```

### Developer Agent

Esegue il ciclo:

```text
analisi repository -> piano -> patch -> test -> correzione -> commit -> PR
```

Non modifica mai direttamente `main` e non può lavorare fuori dai percorsi autorizzati.

### Safety Layer

Valida ogni azione prima dell'esecuzione. Applica allowlist, limiti temporali, limiti di passaggi, modalità simulazione, conferme e arresto di emergenza.

### Event Bus

Pubblica eventi come:

- session_started
- screenshot_captured
- decision_received
- action_validated
- action_executed
- action_failed
- test_started
- test_completed
- session_completed
- session_stopped

## Confini di sicurezza

- niente password nei prompt o nei log;
- niente terminale libero nella prima versione;
- niente cancellazioni o modifiche irreversibili senza consenso;
- niente push su `main`;
- massimo numero di step e tentativi configurabile;
- budget AI separato per sessione e per giorno;
- ogni aggiornamento deve essere reversibile.

## Stato attuale

Il progetto dispone già di acquisizione schermo, controlli di mouse e tastiera, gestione finestre, executor, safety, planner iniziale, Control Center e una prima struttura Agent Loop. La priorità è consolidare AI Client, Workspace, Memory e test prima di aumentare l'autonomia.

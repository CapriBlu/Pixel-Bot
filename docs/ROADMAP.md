# Pixel Bot — Master Roadmap

## Visione

Pixel Bot è un Desktop AI Agent intelligente capace di vedere lo schermo, ragionare sugli obiettivi, agire su Windows, ricordare ciò che ha fatto e contribuire allo sviluppo delle versioni successive di sé stesso in modo controllato.

## Goal finale

Costruire un sistema modulare composto da agenti specializzati:

- Desktop Agent
- Developer Agent
- Vision Agent
- Planning Agent
- Memory Agent
- Voice Agent
- Network Agent
- Knowledge Agent

Tutti gli agenti condividono:

- Workspace persistente
- Memory
- AI Client
- Event Bus
- Knowledge Base
- Safety Layer

## Principi obbligatori

1. Nessuna azione irreversibile senza approvazione.
2. Nessuna modifica diretta al branch principale.
3. Ogni aggiornamento deve essere sviluppato su branch dedicata.
4. Ogni modifica deve essere verificata da test automatici.
5. Ogni decisione importante deve essere registrata.
6. Il merge finale resta sotto controllo umano.
7. Limiti di costo, durata e numero di passaggi devono essere sempre configurabili.

---

## Milestone 0.3 — Agent Foundation

### Goal

Ottenere un Agent Loop completo, osservabile e persistente.

### Requisiti

- [ ] Workspace persistente
- [ ] Memory persistente
- [ ] AI Client collegato al backend condiviso
- [ ] JSON strutturato e validato
- [ ] Goal Manager
- [ ] Planner
- [ ] Agent Loop con massimo numero di passaggi
- [ ] Safety Layer
- [ ] Event System
- [ ] Modalità simulazione
- [ ] Test automatici

### Criterio di completamento

Pixel Bot deve ricevere un obiettivo semplice, acquisire uno screenshot, ottenere una decisione strutturata, validarla, eseguirla, verificare il risultato e registrare l'intera sessione.

---

## Milestone 0.4 — Desktop Agent

### Goal

Permettere a Pixel Bot di completare attività reali su Windows.

### Capacità

- controllo mouse
- controllo tastiera
- gestione finestre
- apertura applicazioni autorizzate
- clipboard
- browser
- file e cartelle in aree autorizzate
- riconoscimento degli elementi visivi
- arresto manuale immediato

### Criterio di completamento

Pixel Bot deve completare in sicurezza un'attività multi-step come aprire un'applicazione, inserire testo e verificare visivamente il risultato.

---

## Milestone 0.5 — Memory

### Goal

Evitare che ogni ciclo riparta da zero.

### Memorie previste

- memoria della sessione
- memoria degli errori
- memoria dei tentativi
- memoria delle applicazioni
- memoria dei repository
- memoria delle soluzioni riuscite

### Criterio di completamento

Il bot deve essere capace di evitare un'azione già fallita e riutilizzare una soluzione precedentemente riuscita.

---

## Milestone 0.6 — Planner

### Goal

Suddividere automaticamente un obiettivo complesso in passi verificabili.

### Criterio di completamento

Per ogni obiettivo il Planner deve generare un piano con step, stato, dipendenze, criterio di successo e strategia di recupero.

---

## Milestone 0.7 — Developer Agent

### Goal

Permettere a Pixel Bot di contribuire allo sviluppo del proprio repository.

### Capacità

- leggere la struttura del repository
- individuare i file coinvolti
- proporre un piano tecnico
- creare e modificare file solo in percorsi autorizzati
- generare patch
- eseguire test
- correggere errori
- creare commit su branch dedicata
- preparare una Pull Request

### Criterio di completamento

Pixel Bot deve ricevere un task di sviluppo semplice, implementarlo, far passare i test e preparare una Pull Request senza modificare `main`.

---

## Milestone 0.8 — Self Improvement

### Goal

Consentire al Developer Agent di proporre miglioramenti al proprio codice.

### Flusso

1. analisi del repository
2. selezione di un miglioramento limitato
3. piano tecnico
4. modifica su branch dedicata
5. test
6. correzione automatica entro un numero massimo di tentativi
7. report dei cambiamenti
8. Pull Request per revisione umana

### Criterio di completamento

Pixel Bot deve produrre autonomamente un aggiornamento utile, limitato, testato e reversibile.

---

## Milestone 1.0 — Autonomous Developer

### Goal

Ricevere una richiesta di sviluppo e completare autonomamente l'intero ciclo fino alla Pull Request.

Esempio:

> Implementa il supporto ai comandi vocali.

Il sistema dovrà:

1. analizzare il progetto;
2. progettare la soluzione;
3. implementarla;
4. scrivere o aggiornare i test;
5. eseguire i test;
6. correggere gli errori;
7. aggiornare la documentazione;
8. creare commit e Pull Request;
9. attendere l'approvazione umana.

---

## Priorità attuale

Lo sviluppo attuale è concentrato sulla **Milestone 0.3 — Agent Foundation**.

Il primo traguardo operativo è:

> Pixel Bot deve riuscire a completare e registrare un loop visivo sicuro con memoria persistente e backend AI condiviso.

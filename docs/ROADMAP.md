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

## Direzione strategica

Pixel Bot non deve diventare una semplice macro o un assistente che esegue comandi fissi. La destinazione è una piattaforma di **automazione desktop assistita dall'intelligenza artificiale**, capace di osservare, comprendere, pianificare, agire, verificare e migliorare progressivamente i propri strumenti mantenendo sicurezza, controllo umano e tracciabilità.

Quando un'automazione o il Developer Agent deve scegliere il prossimo passo di sviluppo, deve privilegiare nell'ordine:

1. affidabilità e sicurezza delle fondamenta;
2. osservabilità, test e recupero dagli errori;
3. qualità del ciclo osservazione → decisione → azione → verifica;
4. modularità e riutilizzo delle capacità;
5. autonomia progressiva, controllata e reversibile.

Una nuova funzionalità non è prioritaria quando rende il sistema più fragile, meno verificabile o meno sicuro.

### Domanda guida

> Qual è il cambiamento più piccolo, sicuro e verificabile che consolida le fondamenta attuali e avvicina Pixel Bot a diventare un assistente operativo e developer AI modulare, affidabile e progressivamente autonomo?

---

# Breve periodo — Consolidare le fondamenta

## Obiettivo

Rendere il nucleo attuale stabile, testabile, osservabile e sicuro prima di ampliare l'autonomia.

## Priorità operative

- stabilizzare `AgentDecision` e la validazione degli output strutturati;
- completare il loop a una sola azione per ciclo;
- introdurre limiti di passi, timeout e stop manuale affidabile;
- distinguere gli stati: in esecuzione, completato, bloccato, fallito e annullato;
- impedire l'esecuzione di output AI non validati;
- prevenire loop ripetitivi e azioni senza effetto;
- gestire retry limitati e strategie alternative;
- salvare checkpoint e report diagnostici;
- consolidare allowlist, conferme e limiti non aggirabili dall'AI;
- mantenere tutti i test verdi e rimuovere warning evitabili;
- applicare modifiche piccole, tracciabili e reversibili;
- mantenere il Developer Loop confinato a branch dedicate.

## Criteri di uscita

Il breve periodo è consolidato quando:

- il loop completa task desktop semplici senza comportamento imprevedibile;
- ogni azione è validata, registrata e interrompibile;
- errori e blocchi non producono loop infiniti;
- i test critici sono stabili e ripetibili;
- il Developer Loop produce modifiche revisionabili;
- il sistema sa fermarsi quando mancano informazioni sufficienti.

---

# Medio periodo — Assistente operativo modulare

## Obiettivo

Trasformare le fondamenta consolidate in una piattaforma capace di affrontare attività reali multi-step tramite componenti e skill specializzate.

## Pilastri

### Computer Vision

- gestione affidabile di uno o più monitor;
- riconoscimento di finestre, pulsanti, campi e messaggi;
- confronto tra screenshot precedenti e successivi;
- rilevamento dei cambiamenti rilevanti dell'interfaccia;
- coordinate ancorate agli elementi visivi invece che soltanto a posizioni fisse.

### Comprensione e pianificazione

- decomposizione degli obiettivi in sotto-obiettivi;
- pianificazione adattiva basata sui risultati;
- stima di rischio e confidenza della prossima azione;
- riconoscimento affidabile del completamento;
- richiesta di chiarimenti in caso di ambiguità.

### Action Engine

- mouse, tastiera e gestione finestre affidabili;
- browser automation controllata;
- integrazione con API quando più sicura della simulazione visiva;
- azioni atomiche, verificabili e annullabili quando possibile;
- adattatori dedicati alle applicazioni più usate.

### Memoria

- cronologia strutturata di decisioni, azioni e risultati;
- checkpoint e ripresa dei task;
- memoria delle strategie fallite;
- separazione tra memoria del task, configurazione e conoscenza del progetto.

### Skill System

Ogni capacità importante deve poter diventare un modulo indipendente, installabile e testabile, ad esempio:

- Browser Skill;
- Git Skill;
- File System Skill;
- Excel Skill;
- Email Skill;
- Developer Skill;
- Desktop Vision Skill.

Ogni skill deve dichiarare azioni disponibili, parametri, permessi, rischi, conferme, condizioni di successo e test.

### Control Center

- inserimento dell'obiettivo;
- visualizzazione di osservazione, decisione e azione proposta;
- conferma, rifiuto, pausa e stop;
- modalità passo-passo e automatica controllata;
- cronologia, log, screenshot e report;
- configurazione di permessi e limiti.

### Developer Agent

- lettura obbligatoria di roadmap, architettura, issue, test e report;
- proposta del prossimo miglioramento coerente con la destinazione;
- patch piccole e verificabili;
- esecuzione e interpretazione dei test;
- correzione iterativa entro limiti definiti;
- branch e pull request dedicate;
- revisione umana obbligatoria prima del merge.

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

1. lettura di `AGENTS.md` e `docs/ROADMAP.md`;
2. analisi del repository;
3. selezione di un miglioramento limitato e coerente con la priorità attuale;
4. piano tecnico;
5. modifica su branch dedicata;
6. test;
7. correzione automatica entro un numero massimo di tentativi;
8. report dei cambiamenti;
9. Pull Request per revisione umana.

### Criterio di completamento

Pixel Bot deve produrre autonomamente un aggiornamento utile, limitato, testato, reversibile e coerente con la roadmap.

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

Lo sviluppo attuale è concentrato sulla **Milestone 0.3 — Agent Foundation** e sul consolidamento delle fondamenta descritto nella roadmap di breve periodo.

Il primo traguardo operativo è:

> Pixel Bot deve riuscire a completare e registrare un loop visivo sicuro con memoria persistente e backend AI condiviso.

Fino al raggiungimento dei criteri di uscita del breve periodo, le nuove funzionalità devono essere considerate secondarie rispetto a stabilità, sicurezza, test, osservabilità e resilienza.

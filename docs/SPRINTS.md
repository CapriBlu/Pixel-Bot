# Pixel Bot — Sprint operativi

## Sprint 1 — Agent Foundation

### Obiettivo

Portare Pixel Bot al punto in cui può completare un loop visivo sicuro, registrare la sessione e preparare il terreno per il primo aggiornamento autonomo.

### Deliverable

- [ ] AI Client completo e configurabile
- [ ] Workspace persistente
- [ ] Memory persistente
- [ ] integrazione Workspace/Memory nell'Agent Loop
- [ ] modalità simulazione
- [ ] limite massimo di step
- [ ] rilevamento azioni ripetute
- [ ] logging eventi
- [ ] test dei modelli e del loop
- [ ] configurazione backend condiviso
- [ ] documentazione di avvio

### Definition of Done

Lo sprint è concluso quando un test end-to-end simulato dimostra che Pixel Bot:

1. crea una sessione;
2. acquisisce o riceve uno screenshot;
3. ottiene una decisione strutturata;
4. valida l'azione;
5. simula o esegue l'azione;
6. registra decisione e risultato;
7. interrompe il ciclo al completamento o al limite;
8. produce un report finale.

## Sprint 2 — Desktop Reliability

### Obiettivo

Rendere affidabili le attività multi-step su Windows.

### Deliverable

- [ ] verifica post-azione
- [ ] recupero dagli errori
- [ ] coordinate e monitor multipli
- [ ] individuazione finestre
- [ ] clipboard controllata
- [ ] browser controllato
- [ ] arresto d'emergenza

## Sprint 3 — Developer Foundation

### Obiettivo

Preparare il primo aggiornamento autonomo del repository.

### Deliverable

- [ ] Repository Reader
- [ ] Developer Planner
- [ ] Workspace Manager per patch
- [ ] Test Runner
- [ ] Git Manager su branch dedicata
- [ ] report delle modifiche
- [ ] Pull Request draft

## Sprint 4 — First Self Update

### Obiettivo

Far realizzare a Pixel Bot un aggiornamento limitato di sé stesso.

### Task candidato

Aggiungere nel Control Center una vista della sessione Agent Loop con numero di step, stato, ultima osservazione e pulsante di stop.

### Definition of Done

- modifica generata su branch dedicata;
- test nuovi o aggiornati;
- test superati;
- documentazione aggiornata;
- Pull Request pronta per revisione umana.

## Stato corrente

**Sprint attivo:** Sprint 1 — Agent Foundation.

**Prossimo task:** PB-001 — Consolidare Workspace e Memory.

# Roadmap

## Sprint corrente — Documentation & MVP Handoff

Obiettivo: rendere Pixel Bot comprensibile, installabile e lavorabile da un altro sviluppatore senza spiegazioni verbali continue.

### Deliverable

- README completo;
- guida installazione e avvio;
- struttura e tecnologie;
- diagramma architetturale;
- flusso dati e comunicazione client-server;
- contratto API previsto;
- MVP e Definition of Done;
- issue GitHub granulari;
- verifica finale da ambiente Windows pulito.

### Ordine di esecuzione

1. Documentazione e inventario del codice.
2. Consolidamento screen capture e controller.
3. Settings, logging ed error handling.
4. OCR e AI Vision dietro feature flag.
5. Test end-to-end e procedura di rilascio MVP.

## Backlog tecnico prioritario

| Priorità | Area | Risultato atteso |
|---|---|---|
| P0 | Screen capture | acquisizione affidabile con metadati e test |
| P0 | Mouse/keyboard | azioni validate, arrestabili e testabili |
| P0 | Error handling | errori strutturati senza crash dell'interfaccia |
| P0 | Logging | tracciamento leggibile e privo di segreti |
| P1 | Settings | configurazione persistente e validata |
| P1 | OCR | testo e bounding box da screenshot |
| P1 | AI Vision | osservazioni JSON con privacy e fallback |
| P1 | MVP E2E | scenario dimostrativo riproducibile |

## Fasi successive

### v0.3 — Vision foundation

- cattura per monitor, finestra e regione;
- OCR locale;
- schema Observation;
- fixture e test visivi;
- redazione dati sensibili.

### v0.4 — AI-assisted planning

- provider Vision configurabile;
- output JSON validato;
- limiti di costo e timeout;
- fallback locale;
- Planner alimentato da osservazioni.

### v0.5 — Reliable execution

- retry controllati;
- verifica post-azione;
- checkpoint;
- persistenza task;
- log strutturati;
- packaging Windows.

### v0.6 — Supervised autonomy

- ciclo osserva-pianifica-agisci-verifica;
- escalation all'utente;
- criteri di arresto;
- rollback;
- integrazione MAGI nelle proposte evolutive.

## Rischi principali

- coordinate fragili rispetto a risoluzione e scaling;
- invio accidentale di dati sensibili nelle immagini;
- piani AI non deterministici;
- automazione che agisce sulla finestra sbagliata;
- retry incontrollati;
- differenze tra ambiente di sviluppo e installazione pulita.

Ogni fase deve ridurre questi rischi attraverso validazione locale, test, conferme e limiti espliciti.
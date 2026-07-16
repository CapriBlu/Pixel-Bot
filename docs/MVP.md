# Minimum Viable Product

## Obiettivo

Dimostrare che Pixel Bot può ricevere un obiettivo semplice, preparare un piano visibile, ottenere il consenso dell'utente ed eseguire azioni desktop limitate e tracciabili su Windows.

## Scenario dimostrativo

1. Installazione da repository pulito.
2. Avvio del Control Center.
3. Acquisizione di uno screenshot.
4. Inserimento di un comando supportato, per esempio aprire Blocco note e scrivere un testo.
5. Visualizzazione del piano.
6. Conferma o annullamento.
7. Esecuzione controllata.
8. Arresto manuale disponibile.
9. Visualizzazione del risultato o dell'errore.
10. Presenza del log dell'operazione.

## Funzioni obbligatorie

- installazione documentata su Windows;
- Control Center avviabile;
- acquisizione schermo;
- parser e Planner per un insieme dichiarato di comandi;
- anteprima del piano;
- validazione Safety;
- controllo mouse e tastiera;
- gestione finestre o apertura di un'app consentita;
- stop dell'esecuzione;
- logging ed error handling;
- configurazione minima;
- test automatici verdi in CI.

## Fuori dall'MVP

- controllo universale di qualsiasi applicazione;
- autonomia senza supervisione;
- memorizzazione permanente di schermate sensibili;
- esecuzione arbitraria di shell;
- auto-modifica autonoma del codice in produzione;
- supporto completo macOS o Linux;
- OCR e AI Vision obbligatori per la demo base.

OCR e AI Vision possono entrare come funzionalità sperimentali, ma non devono bloccare la consegna dell'MVP deterministico.

## Definition of Done

Una funzione è completata quando:

- il comportamento è implementato;
- esistono test appropriati o una motivazione documentata per il test manuale;
- gli errori sono gestiti e mostrati chiaramente;
- non introduce segreti nel repository;
- README o documentazione sono aggiornati;
- la CI è verde;
- un secondo sviluppatore può riprodurre il risultato seguendo istruzioni scritte.

## Criteri di accettazione finali

- clone e installazione in un ambiente Windows pulito senza passaggi nascosti;
- `pytest -q` completato con successo;
- Control Center aperto senza traceback;
- screenshot salvato o mostrato correttamente;
- almeno un piano multi-step generato e visualizzato;
- azione non consentita bloccata da Safety;
- annullamento prima dell'esecuzione funzionante;
- stop durante l'esecuzione funzionante;
- errore del controller trasformato in stato `failed` senza chiudere brutalmente l'app;
- log consultabile con timestamp e contesto;
- nessuna chiave API o dato sensibile nei commit.
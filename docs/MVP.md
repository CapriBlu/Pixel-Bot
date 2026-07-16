# Minimum Viable Product

## Obiettivo

Dimostrare che Pixel Bot può ricevere un obiettivo semplice, preparare un piano visibile, ottenere il consenso dell'utente ed eseguire azioni desktop limitate e tracciabili su Windows.

## Scenario dimostrativo

1. Installare il progetto da un repository pulito.
2. Avviare il Control Center.
3. Acquisire uno screenshot.
4. Inserire un comando supportato.
5. Visualizzare il piano generato.
6. Confermare oppure annullare.
7. Eseguire azioni controllate.
8. Permettere l'arresto manuale.
9. Mostrare il risultato o l'errore.
10. Registrare l'operazione nei log.

Esempio di comando:

`Apri Blocco note e scrivi Ciao da Pixel Bot`

## Funzioni obbligatorie

- installazione documentata su Windows;
- Control Center avviabile;
- acquisizione dello schermo;
- parser per i comandi supportati;
- Planner con passaggi ordinati;
- anteprima del piano;
- conferma prima dell'esecuzione;
- validazione Safety;
- controllo limitato di mouse e tastiera;
- apertura o selezione di applicazioni consentite;
- arresto del piano;
- logging;
- gestione controllata degli errori;
- configurazione minima;
- test automatici funzionanti.

## Funzioni escluse dall'MVP

- controllo universale di qualsiasi programma;
- autonomia completa senza supervisione;
- esecuzione arbitraria di comandi shell;
- conservazione permanente di screenshot sensibili;
- auto-modifica incontrollata del codice;
- supporto completo macOS e Linux;
- OCR obbligatorio per la demo;
- AI Vision obbligatoria per la demo.

OCR e AI Vision possono essere presenti come funzioni sperimentali, ma non devono impedire il completamento dell'MVP deterministico.

## Definition of Done

Una funzione viene considerata completata quando:

- il comportamento previsto è implementato;
- sono presenti test automatici o una procedura manuale documentata;
- gli errori sono gestiti chiaramente;
- non vengono inserite chiavi o password nel repository;
- la documentazione interessata è aggiornata;
- tutti i test risultano verdi;
- un secondo sviluppatore può riprodurre il risultato seguendo istruzioni scritte.

## Criteri di accettazione finali

- installazione su Windows senza passaggi nascosti;
- `pytest -q` completato con successo;
- Control Center aperto senza traceback;
- screenshot acquisito correttamente;
- almeno un piano multi-step generato;
- piano mostrato prima dell'esecuzione;
- azione non consentita bloccata da Safety;
- annullamento prima dell'esecuzione funzionante;
- stop durante l'esecuzione funzionante;
- errore del controller trasformato in stato `failed`;
- interfaccia ancora utilizzabile dopo un errore;
- log consultabile con timestamp e contesto;
- nessuna chiave API o informazione sensibile nei commit.

## Stato verificato

La configurazione locale è stata verificata con:

- Python 3.12.10;
- ambiente virtuale attivo;
- dipendenze installate;
- Control Center funzionante;
- 75 test superati;
- un warning pytest non bloccante relativo alla raccolta della classe `TestRunner`.

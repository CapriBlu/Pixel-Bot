# PB-055 — Pulsante Auto-Evoluzione controllata

PB-055 aggiunge al launcher Windows un pulsante rosso lampeggiante:

**LANCIA AUTO-EVOLUZIONE**

## Comportamento

Il pulsante richiede conferma esplicita e avvia una sessione autonoma limitata:

1. richiede un repository Git pulito;
2. esegue la suite di test;
3. esegue l'audit PB-054 quando disponibile;
4. esegue il gate PB-031 quando disponibile;
5. elabora al massimo una task pendente;
6. applica le modifiche e crea il commit solo con test verdi;
7. non esegue automaticamente il push su GitHub;
8. produce un report in `workspace/auto-evolution/`.

La sessione può essere bloccata creando `workspace/STOP` prima dell'avvio.

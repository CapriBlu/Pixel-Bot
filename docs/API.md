# API previste

## Principi

Le API sono contratti previsti per separare il client desktop da un eventuale orchestratore remoto. Non sono tutte implementate. Ogni endpoint deve essere versionato, autenticato, limitato e incapace di eseguire direttamente azioni sul computer.

Base prevista: `/api/v1`.

## Modelli principali

### Observation

```json
{
  "id": "obs_123",
  "captured_at": "2026-07-16T10:00:00+02:00",
  "screen": {"width": 1920, "height": 1080, "monitor": 1},
  "active_window": {"title": "Notepad", "process": "notepad.exe"},
  "ocr_text": "Example text",
  "elements": [
    {"type": "button", "label": "Save", "bounds": [100, 100, 180, 140], "confidence": 0.94}
  ],
  "sensitive_data_redacted": true
}
```

### ActionProposal

```json
{
  "id": "act_123",
  "name": "click",
  "parameters": {"x": 140, "y": 120},
  "reason": "Select the Save button",
  "risk": "low",
  "requires_confirmation": true
}
```

### Plan

```json
{
  "id": "plan_123",
  "goal": "Save the current document",
  "status": "awaiting_confirmation",
  "steps": [
    {"id": 1, "action": "click", "parameters": {"x": 140, "y": 120}, "status": "pending"}
  ]
}
```

## Endpoint previsti

### `POST /observations`

Invia metadati e, solo quando consentito, un'immagine da analizzare.

Risposta: osservazione strutturata con OCR, elementi e classificazione della schermata.

### `POST /plans`

Input:

```json
{
  "goal": "Open Notepad and write hello",
  "observation_id": "obs_123",
  "capabilities": ["open_app", "write_text"],
  "safety_mode": "supervised"
}
```

Output: piano proposto. Il client deve validarlo localmente.

### `POST /plans/{plan_id}/approve`

Registra l'approvazione dell'utente. Non causa l'esecuzione remota; abilita il client locale a procedere.

### `POST /plans/{plan_id}/events`

Invia eventi come `step_started`, `step_completed`, `step_failed`, `stopped` e `blocked_by_safety`.

### `POST /vision/analyze`

Analizza uno screenshot o una regione e restituisce elementi UI, testo, descrizione e confidenza.

### `POST /ocr/extract`

Estrae testo e bounding box. Deve supportare elaborazione locale come opzione predefinita.

### `GET /settings/schema`

Restituisce lo schema delle impostazioni supportate, senza segreti.

### `GET /health`

Restituisce versione, stato e disponibilità dei provider.

## Errori

Formato previsto:

```json
{
  "error": {
    "code": "SAFETY_BLOCKED",
    "message": "The proposed action is not allowed",
    "details": {"action": "shell_command"},
    "retryable": false,
    "request_id": "req_123"
  }
}
```

Codici iniziali:

- `INVALID_REQUEST`;
- `UNAUTHORIZED`;
- `RATE_LIMITED`;
- `VISION_TIMEOUT`;
- `OCR_FAILED`;
- `PLANNING_FAILED`;
- `SAFETY_BLOCKED`;
- `CONFIRMATION_REQUIRED`;
- `EXECUTION_FAILED`;
- `PROVIDER_UNAVAILABLE`.

## Sicurezza e privacy

- TLS obbligatorio;
- immagini non conservate per impostazione predefinita;
- redazione locale di password, token e dati sensibili;
- limiti di dimensione e frequenza;
- identificatore dispositivo revocabile;
- log senza contenuto sensibile;
- consenso esplicito prima dell'invio a provider esterni;
- validazione finale sempre sul client.

## Versionamento

Modifiche incompatibili richiedono una nuova versione dell'API. Ogni payload deve poter includere `schema_version` e ogni risposta deve includere un `request_id` per diagnosi.
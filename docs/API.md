# API previste

## Scopo

Le API consentiranno di separare il client desktop di Pixel Bot da un eventuale server di orchestrazione.

Le API non devono mai controllare direttamente mouse, tastiera o applicazioni del computer. Il server può proporre azioni, ma il client locale deve sempre validarle tramite il livello Safety.

Base prevista: `/api/v1`.

## Modelli principali

### Observation

Rappresenta ciò che Pixel Bot osserva sullo schermo.

```json
{
  "id": "obs_123",
  "captured_at": "2026-07-16T10:00:00+02:00",
  "screen": {
    "width": 1920,
    "height": 1080,
    "monitor": 1
  },
  "active_window": {
    "title": "Notepad",
    "process": "notepad.exe"
  },
  "ocr_text": "Example text",
  "elements": [
    {
      "type": "button",
      "label": "Save",
      "bounds": [100, 100, 180, 140],
      "confidence": 0.94
    }
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
    {
      "id": 1,
      "action": "click",
      "parameters": {"x": 140, "y": 120},
      "status": "pending"
    }
  ]
}
```

## Endpoint previsti

- `POST /observations`
- `POST /plans`
- `POST /plans/{plan_id}/approve`
- `POST /plans/{plan_id}/events`
- `POST /vision/analyze`
- `POST /ocr/extract`
- `GET /settings/schema`
- `GET /health`

## Formato degli errori

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

- `INVALID_REQUEST`
- `UNAUTHORIZED`
- `RATE_LIMITED`
- `VISION_TIMEOUT`
- `OCR_FAILED`
- `PLANNING_FAILED`
- `SAFETY_BLOCKED`
- `CONFIRMATION_REQUIRED`
- `EXECUTION_FAILED`
- `PROVIDER_UNAVAILABLE`

## Sicurezza e privacy

- HTTPS obbligatorio;
- immagini non conservate per impostazione predefinita;
- redazione locale di password, token e dati sensibili;
- consenso esplicito prima dell'invio di screenshot;
- timeout e limiti di frequenza;
- log privi di segreti;
- validazione finale sempre eseguita sul client;
- nessuna azione remota diretta su mouse e tastiera.

## Versionamento

Ogni modifica incompatibile richiede una nuova versione dell'API. Ogni risposta dovrebbe includere un `request_id` e ogni payload dovrebbe supportare un campo `schema_version`.

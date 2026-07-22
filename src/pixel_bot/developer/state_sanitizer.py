from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

_SECRET_KEYS = {"api_key", "authorization", "password", "secret", "token", "cookie", "openai_api_key"}
_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(OPENAI_API_KEY\s*[=:]\s*)[^\s\"']+"),
    re.compile(r"(?i)(authorization:\s*bearer\s+)[^\s]+"),
]


def sanitize_state(value: Any) -> Any:
    value = deepcopy(value)
    return _sanitize(value)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in _SECRET_KEYS:
                cleaned[key] = "[REDACTED]"
            else:
                cleaned[key] = _sanitize(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, str):
        text = value
        for pattern in _PATTERNS:
            text = pattern.sub(lambda m: (m.group(1) if m.lastindex else "") + "[REDACTED]", text)
        return text
    return value

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .state_collector import StateCollector
from .state_sanitizer import sanitize_state
from .state_tools import SafeToolRegistry


_CHECKLIST_LINE = re.compile(
    r"^\s*(?P<id>\d+)[\)\.\-:]\s+(?P<text>\S.*)$"
)
_TERMINAL_STATUSES = {"
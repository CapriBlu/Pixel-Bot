from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pixel_bot.developer.models import TestResult


@dataclass(slots=True)
class TestRunner:
    repository_root: Path
    timeout_seconds: float = 180.0
    allowed_executables: tuple[str, ...] = ("pytest", "python", "py")

    def run(self, command: list[str]) -> TestResult:
        if not command:
            raise ValueError("Il comando di test non può essere vuoto.")
        executable = Path(command[0]).name.lower()
        if executable not in self.allowed_executables:
            raise ValueError(f"Comando di test non autorizzato: {command[0]}")
        environment = os.environ.copy()
        src_path = str((self.repository_root / "src").resolve())
        current_pythonpath = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = (
            src_path if not current_pythonpath else src_path + os.pathsep + current_pythonpath
        )
        completed = subprocess.run(
            command,
            cwd=self.repository_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        return TestResult(
            command=list(command),
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

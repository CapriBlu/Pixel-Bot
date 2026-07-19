from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _run(root: Path, command: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "command": command,
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": command, "return_code": -1, "stdout": "", "stderr": str(exc)}


@dataclass(slots=True)
class StateCollector:
    repository_root: Path

    def collect(self, goal: str, include_diff: bool = True) -> dict[str, Any]:
        root = self.repository_root.resolve()
        git_status = _run(root, ["git", "status", "--short"])
        branch = _run(root, ["git", "branch", "--show-current"])
        head = _run(root, ["git", "rev-parse", "HEAD"])
        recent = _run(root, ["git", "log", "-5", "--pretty=format:%h %s"])
        diff = _run(root, ["git", "diff", "--no-ext-diff", "--unified=2"], timeout=45) if include_diff else None

        python_path = self._python_path(root)
        pytest = _run(root, [str(python_path), "-m", "pytest", "-q"], timeout=180)

        package: dict[str, Any] = {
            "schema_version": "1.0",
            "goal": goal,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "repository": {
                "path": str(root),
                "branch": branch["stdout"],
                "head": head["stdout"],
                "git_status": git_status["stdout"].splitlines() if git_status["stdout"] else [],
                "recent_commits": recent["stdout"].splitlines() if recent["stdout"] else [],
            },
            "tests": {
                "command": pytest["command"],
                "return_code": pytest["return_code"],
                "passed": pytest["return_code"] == 0,
                "stdout_tail": pytest["stdout"][-6000:],
                "stderr_tail": pytest["stderr"][-3000:],
            },
            "runtime": {
                "platform": platform.platform(),
                "python": platform.python_version(),
                "python_executable": str(python_path),
                "disk_free_bytes": shutil.disk_usage(root).free,
            },
            "safety": {
                "automatic": ["read_file", "list_directory", "get_git_status", "get_git_diff", "run_pytest"],
                "approval_required": ["commit", "push", "merge", "reset", "delete", "admin"],
            },
        }
        if diff is not None:
            package["repository"]["diff"] = diff["stdout"][-20000:]
        return package

    @staticmethod
    def _python_path(root: Path) -> Path:
        candidates = [
            root / ".venv" / "Scripts" / "python.exe",
            root / ".venv" / "bin" / "python",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return Path(os.environ.get("PYTHON", "python"))

    def write(self, goal: str, output_dir: Path | None = None) -> Path:
        target_dir = output_dir or self.repository_root / "workspace" / "openai-state-bridge"
        target_dir.mkdir(parents=True, exist_ok=True)
        output = target_dir / "state-package.json"
        output.write_text(json.dumps(self.collect(goal), indent=2, ensure_ascii=False), encoding="utf-8")
        return output

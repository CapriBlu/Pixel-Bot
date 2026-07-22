from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable


class SafeToolRegistry:
    def __init__(self, repository_root: Path) -> None:
        self.root = repository_root.resolve()
        self._tools: dict[str, Callable[..., Any]] = {
            "get_git_status": self.get_git_status,
            "get_git_diff": self.get_git_diff,
            "read_file": self.read_file,
            "list_directory": self.list_directory,
            "run_pytest": self.run_pytest,
        }

    @property
    def schemas(self) -> list[dict[str, Any]]:
        return [
            {"type": "function", "name": "get_git_status", "description": "Read git working tree status.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}, "strict": True},
            {"type": "function", "name": "get_git_diff", "description": "Read the current git diff.", "parameters": {"type": "object", "properties": {"path": {"type": ["string", "null"]}}, "required": ["path"], "additionalProperties": False}, "strict": True},
            {"type": "function", "name": "read_file", "description": "Read a UTF-8 project file inside the repository.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "minimum": 1, "maximum": 30000}}, "required": ["path", "max_chars"], "additionalProperties": False}, "strict": True},
            {"type": "function", "name": "list_directory", "description": "List a directory inside the repository.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"], "additionalProperties": False}, "strict": True},
            {"type": "function", "name": "run_pytest", "description": "Run the local pytest suite safely.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}, "strict": True},
        ]

    def execute(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            return {"ok": False, "error": f"Tool not allowed: {name}"}
        try:
            return {"ok": True, "result": self._tools[name](**arguments)}
        except Exception as exc:  # defensive boundary for model-requested tools
            return {"ok": False, "error": str(exc)}

    def _safe_path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Path outside repository")
        return candidate

    def get_git_status(self) -> str:
        return self._run(["git", "status", "--short"])

    def get_git_diff(self, path: str | None) -> str:
        command = ["git", "diff", "--no-ext-diff", "--unified=3"]
        if path:
            safe = self._safe_path(path)
            command.extend(["--", str(safe.relative_to(self.root))])
        return self._run(command)[-30000:]

    def read_file(self, path: str, max_chars: int) -> str:
        safe = self._safe_path(path)
        if safe.name == ".env" or ".git" in safe.parts:
            raise ValueError("Protected file")
        return safe.read_text(encoding="utf-8", errors="replace")[:max_chars]

    def list_directory(self, path: str) -> list[str]:
        safe = self._safe_path(path)
        return sorted(str(item.relative_to(self.root)) for item in safe.iterdir())[:500]

    def run_pytest(self) -> str:
        python = self.root / ".venv" / "Scripts" / "python.exe"
        executable = str(python if python.exists() else "python")
        return self._run([executable, "-m", "pytest", "-q"], timeout=180)[-12000:]

    def _run(self, command: list[str], timeout: int = 45) -> str:
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        return json.dumps({"return_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, ensure_ascii=False)

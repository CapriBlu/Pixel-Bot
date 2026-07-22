from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FileDecision:
    path: str
    status: str
    category: str
    action: str
    confidence: float
    reason: str
    source: str = "local"


class RepositoryIntelligence:
    SAFE_SOURCE_SUFFIXES = {
        ".py", ".cs", ".ps1", ".cmd", ".bat", ".json", ".toml", ".yaml", ".yml",
        ".md", ".txt", ".ico", ".svg", ".html", ".css", ".js", ".ts", ".tsx",
        ".png", ".jpg", ".jpeg", ".webp",
    }
    TEMP_SUFFIXES = {".bak", ".tmp", ".log", ".pyc"}
    PROTECTED_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}

    def __init__(self, root: Path, model: str | None = None) -> None:
        self.root = root.resolve()
        self.model = model or os.getenv("PIXEL_OPENAI_MODEL", "gpt-5")

    def run(self, goal: str = "Consolidare automaticamente il repository", use_openai: bool = True) -> dict[str, Any]:
        before = self._git_status_entries()
        decisions = [self._classify_local(status, path) for status, path in before]
        ambiguous = [d for d in decisions if d.action == "inspect"]
        openai_error = None
        if ambiguous and use_openai:
            try:
                ai_decisions = self._classify_with_openai(goal, ambiguous)
                by_path = {d.path: d for d in ai_decisions}
                decisions = [by_path.get(d.path, d) for d in decisions]
            except Exception as exc:
                openai_error = str(exc)

        stageable = [
            d.path for d in decisions
            if d.action == "stage" and d.confidence >= 0.90 and self._is_safe_stage_path(d.path)
        ]
        staged: list[str] = []
        if stageable:
            result = subprocess.run(
                ["git", "add", "--", *stageable], cwd=self.root, capture_output=True,
                text=True, encoding="utf-8", errors="replace", check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "git add failed")
            staged = stageable

        tests = self._run_tests()
        after = self._git_status_entries()
        state = "VERDE" if tests["return_code"] == 0 and not after else "ARANCIONE"
        if tests["return_code"] != 0:
            state = "ROSSO"

        return {
            "update": "PB-033",
            "goal": goal,
            "timestamp": datetime.now().astimezone().isoformat(),
            "state": state,
            "openai_used": bool(ambiguous and use_openai and openai_error is None),
            "openai_error": openai_error,
            "decisions": [asdict(d) for d in decisions],
            "staged_automatically": staged,
            "tests": tests,
            "working_tree_after": [{"status": s, "path": p} for s, p in after],
            "safety": {
                "performed": ["read repository", "classify files", "git add safe files", "run pytest"],
                "never_performed": ["delete", "commit", "push", "merge", "reset", "read .env"],
            },
        }

    def _classify_local(self, status: str, path: str) -> FileDecision:
        p = Path(path)
        lower_parts = {part.lower() for part in p.parts}
        suffix = p.suffix.lower()
        name = p.name.lower()

        if name in self.PROTECTED_NAMES or name.startswith(".env"):
            return FileDecision(path, status, "secret", "ignore", 1.0, "File potenzialmente segreto")
        if ".git" in lower_parts or ".venv" in lower_parts or "__pycache__" in lower_parts:
            return FileDecision(path, status, "generated", "ignore", 1.0, "Cartella tecnica o generata")
        if suffix in self.TEMP_SUFFIXES or name.endswith(".pixelbot.bak"):
            return FileDecision(path, status, "backup_or_temporary", "ignore", 1.0, "Backup o file temporaneo")
        if p.parts and p.parts[0].lower() == "workspace":
            return FileDecision(path, status, "runtime_report", "ignore", 1.0, "Report runtime non versionato")
        if path.startswith(("src/", "tests/", "launcher/")):
            return FileDecision(path, status, "project_code", "stage", 0.99, "Percorso strutturale del progetto")
        if suffix in {".py", ".cs", ".ps1", ".cmd", ".bat", ".toml", ".yaml", ".yml"}:
            return FileDecision(path, status, "project_code", "stage", 0.97, "Codice o configurazione del progetto")
        if suffix in {".ico", ".svg"}:
            return FileDecision(path, status, "project_asset", "stage", 0.96, "Asset applicativo")
        if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            return FileDecision(path, status, "ambiguous_image", "inspect", 0.55, "Immagine da correlare al progetto")
        if suffix in self.SAFE_SOURCE_SUFFIXES:
            return FileDecision(path, status, "project_file", "stage", 0.92, "Tipo file compatibile col progetto")
        return FileDecision(path, status, "unknown", "inspect", 0.40, "Tipo o ruolo non determinato")

    def _classify_with_openai(self, goal: str, ambiguous: list[FileDecision]) -> list[FileDecision]:
        from openai import OpenAI
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY non configurata")

        items = []
        for decision in ambiguous:
            path = decision.path
            safe = self._safe_path(path)
            metadata: dict[str, Any] = {"path": path, "suffix": safe.suffix.lower(), "size": safe.stat().st_size if safe.exists() else None}
            if safe.exists() and safe.is_file() and safe.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".ico"}:
                metadata["preview"] = safe.read_text(encoding="utf-8", errors="replace")[:4000]
            items.append(metadata)

        schema = {
            "type": "object",
            "properties": {
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "category": {"type": "string"},
                            "action": {"type": "string", "enum": ["stage", "ignore", "ask"]},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "reason": {"type": "string"},
                        },
                        "required": ["path", "category", "action", "confidence", "reason"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["files"],
            "additionalProperties": False,
        }
        client = OpenAI()
        response = client.responses.create(
            model=self.model,
            instructions=(
                "Classifica esclusivamente i file elencati per il repository Pixel Bot. "
                "Usa stage solo se il file e chiaramente parte del progetto e non contiene segreti. "
                "Usa ignore per output temporanei e ask quando resta dubbio. Non proporre eliminazioni."
            ),
            input=json.dumps({"goal": goal, "files": items}, ensure_ascii=False),
            text={"format": {"type": "json_schema", "name": "repository_file_plan", "strict": True, "schema": schema}},
            store=False,
        )
        payload = json.loads(response.output_text)
        original = {d.path: d for d in ambiguous}
        output: list[FileDecision] = []
        for item in payload.get("files", []):
            path = item["path"]
            if path not in original:
                continue
            action = item["action"]
            confidence = float(item["confidence"])
            # AI decisions are executable only with very high confidence.
            if action == "stage" and confidence < 0.90:
                action = "ask"
            output.append(FileDecision(path, original[path].status, item["category"], action, confidence, item["reason"], "openai"))
        return output

    def _is_safe_stage_path(self, path: str) -> bool:
        safe = self._safe_path(path)
        if safe.name.lower() in self.PROTECTED_NAMES or safe.name.lower().startswith(".env"):
            return False
        return safe.exists() and safe.is_file()

    def _safe_path(self, relative: str) -> Path:
        candidate = (self.root / relative).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("Path outside repository")
        return candidate

    def _git_status_entries(self) -> list[tuple[str, str]]:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"], cwd=self.root, capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
        entries: list[tuple[str, str]] = []
        chunks = result.stdout.split(b"\0")
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            if not chunk:
                i += 1
                continue
            text = chunk.decode("utf-8", errors="replace")
            status, path = text[:2], text[3:]
            if status[0] in {"R", "C"} and i + 1 < len(chunks):
                i += 1
                path = chunks[i].decode("utf-8", errors="replace")
            entries.append((status, path))
            i += 1
        return entries

    def _run_tests(self) -> dict[str, Any]:
        python = self.root / ".venv" / "Scripts" / "python.exe"
        executable = str(python if python.exists() else "python")
        result = subprocess.run(
            [executable, "-m", "pytest", "-q"], cwd=self.root, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=240, check=False,
        )
        return {"return_code": result.returncode, "stdout": result.stdout[-12000:], "stderr": result.stderr[-6000:]}

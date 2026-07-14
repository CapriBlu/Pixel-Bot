from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pixel_bot.agent.ai_client import AIClientConfig
from pixel_bot.agent.budget import BudgetState
from pixel_bot.agent.workspace import Workspace
from pixel_bot.developer.models import DevelopmentPlan, DevelopmentTask, FileChange, RepositorySnapshot

Transport = Callable[[Request, float], dict[str, Any]]

_FILE_CHANGES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["path", "content", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["changes"],
    "additionalProperties": False,
}


@dataclass(slots=True)
class DeveloperAIProvider:
    repository_root: Path
    config: AIClientConfig
    workspace: Workspace | None = None
    transport: Transport | None = None
    simulated_changes: Iterable[list[FileChange]] | None = None
    max_file_chars: int = 20_000
    max_total_chars: int = 80_000
    budget: BudgetState = field(init=False)
    _simulation_iterator: Any = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        self.budget = BudgetState(
            max_requests=self.config.max_requests_per_task,
            max_estimated_cost=self.config.max_estimated_cost,
            estimated_cost_per_request=self.config.estimated_cost_per_request,
        )
        if self.simulated_changes is not None:
            self._simulation_iterator = iter(self.simulated_changes)

    def __call__(
        self,
        task: DevelopmentTask,
        snapshot: RepositorySnapshot,
        plan: DevelopmentPlan,
    ) -> list[FileChange]:
        self.budget.ensure_available()
        if self.config.dry_run:
            changes = self._next_simulated_changes()
            self.budget.record_request()
            self._record_usage("simulation", len(changes))
            return changes

        if not self.config.endpoint:
            raise RuntimeError("Endpoint AI non configurato.")

        context = self._build_context(task, snapshot, plan)
        if self.config.provider == "openai":
            payload = self._build_openai_payload(context)
        else:
            payload = context

        request = Request(
            self.config.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        response = self._send(request)
        raw_changes = (
            self._extract_openai_changes(response)
            if self.config.provider == "openai"
            else response.get("changes", response.get("file_changes"))
        )
        changes = self._parse_changes(raw_changes)
        self.budget.record_request()
        self._record_usage(self.config.provider, len(changes))
        return changes

    def _build_context(
        self,
        task: DevelopmentTask,
        snapshot: RepositorySnapshot,
        plan: DevelopmentPlan,
    ) -> dict[str, Any]:
        return {
            "task": {
                "task_id": task.task_id,
                "title": task.title,
                "objective": task.objective,
                "acceptance_criteria": task.acceptance_criteria,
                "allowed_paths": task.allowed_paths,
                "test_command": task.test_command,
            },
            "plan": plan.to_dict(),
            "repository": {
                "files": snapshot.files,
                "relevant_file_contents": self._read_relevant_files(plan.relevant_files),
            },
        }

    def _build_openai_payload(self, context: dict[str, Any]) -> dict[str, Any]:
        instructions = (
            "Sei il Developer Agent di Pixel Bot. Proponi esclusivamente modifiche complete "
            "di file necessarie per completare il task. Non modificare percorsi fuori da "
            "task.allowed_paths. Ogni file deve avere path, content completo e reason."
        )
        return {
            "model": self.config.model,
            "instructions": instructions,
            "input": json.dumps(context, ensure_ascii=False),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "file_changes_v1",
                    "strict": True,
                    "schema": _FILE_CHANGES_SCHEMA,
                }
            },
        }

    @staticmethod
    def _extract_openai_changes(response: dict[str, Any]) -> Any:
        direct_text = response.get("output_text")
        if isinstance(direct_text, str):
            return DeveloperAIProvider._decode_openai_json(direct_text).get("changes")

        output = response.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict) or item.get("type") != "message":
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for part in content:
                    if not isinstance(part, dict) or part.get("type") != "output_text":
                        continue
                    text = part.get("text")
                    if isinstance(text, str):
                        return DeveloperAIProvider._decode_openai_json(text).get("changes")
        raise RuntimeError("La Responses API non contiene output JSON strutturato.")

    @staticmethod
    def _decode_openai_json(text: str) -> dict[str, Any]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as error:
            raise RuntimeError("La Responses API ha restituito output_text non JSON.") from error
        if not isinstance(payload, dict):
            raise RuntimeError("La Responses API deve restituire un oggetto JSON.")
        return payload

    def _read_relevant_files(self, paths: list[str]) -> list[dict[str, str]]:
        items: list[dict[str, str]] = []
        total = 0
        for relative_path in paths:
            target = (self.repository_root / relative_path).resolve()
            try:
                target.relative_to(self.repository_root)
            except ValueError:
                continue
            if not target.is_file():
                continue
            try:
                content = target.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            content = content[: self.max_file_chars]
            remaining = self.max_total_chars - total
            if remaining <= 0:
                break
            content = content[:remaining]
            items.append({"path": relative_path, "content": content})
            total += len(content)
        return items

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"
        return headers

    def _send(self, request: Request) -> dict[str, Any]:
        if self.transport is not None:
            payload = self.transport(request, self.config.timeout_seconds)
        else:
            try:
                with urlopen(request, timeout=self.config.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"Backend AI HTTP {error.code}: {detail}") from error
            except URLError as error:
                raise RuntimeError(f"Backend AI non raggiungibile: {error.reason}") from error
            except json.JSONDecodeError as error:
                raise RuntimeError("Il backend AI ha restituito JSON non valido.") from error
        if not isinstance(payload, dict):
            raise RuntimeError("Il backend AI deve restituire un oggetto JSON.")
        return payload

    @staticmethod
    def _parse_changes(payload: Any) -> list[FileChange]:
        if not isinstance(payload, list):
            raise RuntimeError("La risposta AI non contiene una lista di modifiche.")
        changes: list[FileChange] = []
        for item in payload:
            if not isinstance(item, dict):
                raise RuntimeError("Ogni modifica AI deve essere un oggetto JSON.")
            path = item.get("path")
            content = item.get("content")
            if not isinstance(path, str) or not path.strip():
                raise RuntimeError("Una modifica AI contiene un path non valido.")
            if not isinstance(content, str):
                raise RuntimeError("Una modifica AI contiene content non valido.")
            changes.append(
                FileChange(path=path, content=content, reason=str(item.get("reason", "")))
            )
        return changes

    def _next_simulated_changes(self) -> list[FileChange]:
        if self._simulation_iterator is None:
            return []
        try:
            return list(next(self._simulation_iterator))
        except StopIteration as error:
            raise RuntimeError("Modifiche simulate esaurite.") from error

    def _record_usage(self, mode: str, changes_count: int) -> None:
        if self.workspace is not None:
            self.workspace.append_event(
                "developer_ai_request",
                {
                    "mode": mode,
                    "changes_count": changes_count,
                    "budget": self.budget.to_dict(),
                },
            )

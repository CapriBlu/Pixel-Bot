from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 12000
MAX_TOOL_ROUNDS = 4
MAX_TOOLS_PER_ROUND = 6
PROJECT_MARKERS = (
    "README.md", "README.txt", "pyproject.toml", "requirements.txt", "pytest.ini",
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "pom.xml", "build.gradle", "build.gradle.kts", "Cargo.toml", "go.mod",
)


def emit(name: str, value: str) -> None:
    encoded = base64.b64encode((value or "").encode("utf-8")).decode("ascii")
    print(f"{name}={encoded}")


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def extract_output_text(payload: dict) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    parts: list[str] = []
    for item in payload.get("output", []) or []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) or []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def run_bounded(command: list[str], cwd: Path, timeout: int = 30, env: dict[str, str] | None = None) -> dict:
    try:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            env=merged_env,
        )
        output = result.stdout or ""
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        return {
            "command": command,
            "exit_code": result.returncode,
            "output": output.strip()[:MAX_OUTPUT_CHARS],
        }
    except FileNotFoundError:
        return {"command": command, "exit_code": 127, "output": "Comando non disponibile."}
    except subprocess.TimeoutExpired as exc:
        partial = ""
        if exc.stdout:
            partial += exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode("utf-8", "replace")
        if exc.stderr:
            partial += exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode("utf-8", "replace")
        return {"command": command, "exit_code": 124, "output": (partial + "\nTimeout del controllo.").strip()[:MAX_OUTPUT_CHARS]}
    except Exception as exc:
        return {"command": command, "exit_code": 1, "output": f"Errore diagnostico: {exc}"}


def safe_read_text(path: Path, max_chars: int = 8000) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")[:max_chars]
    except Exception as exc:
        return f"[Impossibile leggere {path.name}: {exc}]"


def discover_project_context(repo: Path, user_request: str) -> tuple[dict, Path]:
    discovery: dict[str, Any] = {
        "version": "active-discovery-v2",
        "request": user_request,
        "repository": str(repo),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "policy": {
            "mode": "automatic-safe-local",
            "writes_allowed": False,
            "network_tools_used": False,
            "max_tool_rounds": MAX_TOOL_ROUNDS,
        },
        "checks": [],
        "project_markers": {},
        "top_level_entries": [],
    }
    commands = [
        ["git", "status", "--short", "--branch"],
        ["git", "branch", "--show-current"],
        ["git", "log", "-n", "5", "--oneline"],
        ["git", "diff", "--stat"],
        ["git", "diff", "--cached", "--stat"],
    ]
    for command in commands:
        discovery["checks"].append(run_bounded(command, repo, timeout=15))

    try:
        entries = sorted(repo.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        discovery["top_level_entries"] = [
            {"name": p.name, "type": "directory" if p.is_dir() else "file"}
            for p in entries[:150]
            if p.name not in {".git", ".venv", "venv", "node_modules", "__pycache__"}
        ]
    except Exception as exc:
        discovery["top_level_entries_error"] = str(exc)

    for marker in PROJECT_MARKERS:
        path = repo / marker
        if path.exists() and path.is_file():
            discovery["project_markers"][marker] = safe_read_text(path)

    found_projects: list[str] = []
    for pattern in ("*.sln", "*.csproj", "*.fsproj"):
        found_projects.extend(path.name for path in repo.glob(pattern))
        if (repo / "src").exists():
            found_projects.extend(str(path.relative_to(repo)) for path in (repo / "src").glob(pattern))
    discovery["project_files"] = sorted(set(found_projects))[:100]

    report_dir = repo / "workspace" / "active-discovery"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"discovery-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
    report_path.write_text(json.dumps(discovery, ensure_ascii=False, indent=2), encoding="utf-8")
    return discovery, report_path


def compact(value: Any, max_chars: int = 40000) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)[:max_chars]


def run_magi(repo: Path, user_request: str, context: dict, phase: str) -> tuple[dict, Path]:
    src = repo / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from pixel_bot.magi.council import MagiCouncil
    from pixel_bot.magi.memory import MagiMemoryStore
    from pixel_bot.magi.models import MagiProposal, MagiRole
    from pixel_bot.magi.providers import build_default_providers
    from pixel_bot.magi.reporting import write_decision_report

    memory_dir = repo / "workspace" / "magi-memory"
    memory_store = MagiMemoryStore(memory_dir)
    memories = {role: memory_store.load(role, limit=20) for role in MagiRole}

    proposal = MagiProposal(
        goal=user_request,
        context=(
            f"Fase MAGI: {phase}. Pixel Bot puo colmare autonomamente le lacune tramite un ciclo "
            "di strumenti locali allowlisted, sicuri, limitati e registrati. Non chiedere conferma "
            "per letture, test, lint o diagnostica non distruttiva. Chiedere conferma solo quando "
            "serve scrivere, eliminare, installare, pubblicare, usare privilegi o compiere azioni "
            "irreversibili. Usa esclusivamente i risultati reali allegati.\n\nCONTESTO:\n" + compact(context)
        ),
        constraints=(
            "Proteggere dati, sistema e repository.",
            "Preferire azioni reversibili e verificabili.",
            "Eseguire automaticamente i controlli locali sicuri necessari.",
            "Una sola approvazione deve coprire un piano di modifica delimitato.",
            "Non inventare risultati di strumenti non eseguiti.",
        ),
    )
    decision = MagiCouncil(build_default_providers(memories)).deliberate(proposal)
    report_dir = repo / "workspace" / "magi-gui"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"magi-{phase}-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
    write_decision_report(decision, report_path)

    for opinion in decision.opinions:
        memory_store.append(
            role=opinion.role,
            proposal_goal=proposal.goal,
            opinion=opinion,
            final_status=decision.status,
        )
    return decision.to_dict(), report_path


def openai_text(api_key: str, model: str, instructions: str, input_text: str, timeout: int) -> str:
    body = json.dumps(
        {"model": model, "instructions": instructions, "input": input_text},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    answer = extract_output_text(payload)
    if not answer:
        raise RuntimeError("La Responses API non ha restituito testo.")
    return answer


def parse_json_object(text: str) -> dict:
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean = "\n".join(lines).strip()
    start = clean.find("{")
    end = clean.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Risposta del planner non JSON.")
    value = json.loads(clean[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("Il planner non ha restituito un oggetto JSON.")
    return value


def resolve_safe_relative(repo: Path, raw_path: str) -> Path:
    candidate = (repo / raw_path).resolve()
    if repo != candidate and repo not in candidate.parents:
        raise ValueError("Percorso esterno al repository non consentito.")
    blocked = {".env", ".git", "id_rsa", "id_ed25519"}
    if any(part.lower() in blocked for part in candidate.relative_to(repo).parts):
        raise ValueError("Percorso sensibile non consentito.")
    return candidate


def execute_safe_tool(repo: Path, request: dict) -> dict:
    name = str(request.get("name", "")).strip()
    args = request.get("arguments") if isinstance(request.get("arguments"), dict) else {}
    result: dict[str, Any] = {"name": name, "arguments": args, "safe": True}

    if name == "pytest_quiet":
        tool_result = run_bounded(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            repo,
            timeout=180,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )
    elif name == "git_status":
        tool_result = run_bounded(["git", "status", "--short", "--branch"], repo, 20)
    elif name == "git_recent_log":
        count = max(1, min(int(args.get("count", 10)), 30))
        tool_result = run_bounded(["git", "log", "-n", str(count), "--oneline", "--decorate"], repo, 20)
    elif name == "git_diff_stat":
        tool_result = run_bounded(["git", "diff", "--stat"], repo, 20)
    elif name == "git_count_ahead":
        branch = run_bounded(["git", "branch", "--show-current"], repo, 15)
        current = branch.get("output", "").strip()
        if not current:
            tool_result = {"command": [], "exit_code": 1, "output": "Branch corrente non rilevato."}
        else:
            upstream = run_bounded(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], repo, 15)
            upstream_name = upstream.get("output", "").strip()
            if upstream.get("exit_code") != 0 or not upstream_name:
                tool_result = {"command": [], "exit_code": 1, "output": "Upstream non configurato."}
            else:
                tool_result = run_bounded(["git", "rev-list", "--count", f"{upstream_name}..{current}"], repo, 20)
    elif name == "inspect_file_bytes":
        raw_path = str(args.get("path", "requirements.txt"))
        byte_count = max(16, min(int(args.get("byte_count", 256)), 2048))
        path = resolve_safe_relative(repo, raw_path)
        data = path.read_bytes()[:byte_count]
        tool_result = {
            "command": ["internal-read-bytes", raw_path, str(byte_count)],
            "exit_code": 0,
            "output": repr(data),
            "contains_null_bytes": b"\x00" in data,
            "size_bytes": path.stat().st_size,
        }
    elif name == "read_file_excerpt":
        raw_path = str(args.get("path", "README.md"))
        max_chars = max(200, min(int(args.get("max_chars", 5000)), 12000))
        path = resolve_safe_relative(repo, raw_path)
        tool_result = {
            "command": ["internal-read-text", raw_path],
            "exit_code": 0,
            "output": safe_read_text(path, max_chars),
        }
    elif name == "list_project_files":
        max_depth = max(1, min(int(args.get("max_depth", 2)), 4))
        files: list[str] = []
        for path in repo.rglob("*"):
            try:
                rel = path.relative_to(repo)
            except ValueError:
                continue
            if len(rel.parts) > max_depth:
                continue
            if any(part in {".git", ".venv", "venv", "node_modules", "__pycache__"} for part in rel.parts):
                continue
            files.append(str(rel) + ("/" if path.is_dir() else ""))
            if len(files) >= 500:
                break
        tool_result = {"command": ["internal-list-files"], "exit_code": 0, "output": "\n".join(sorted(files))}
    else:
        return {"name": name, "safe": False, "exit_code": 126, "output": "Strumento non consentito dalla allowlist."}

    result.update(tool_result)
    return result


def autonomous_tool_loop(
    api_key: str,
    model: str,
    timeout: int,
    repo: Path,
    user_request: str,
    discovery: dict,
    initial_magi: dict,
) -> tuple[str, list[dict], int]:
    tool_history: list[dict] = []
    planner_instructions = """Sei il planner operativo di Pixel Bot MAGI Brain v5.
Devi decidere se la richiesta puo gia ricevere una risposta completa oppure se servono ulteriori informazioni locali.
Quando mancano dati recuperabili in sicurezza, non chiedere conferma all'utente: richiedi strumenti allowlisted.

Rispondi ESCLUSIVAMENTE con un singolo oggetto JSON valido, senza markdown, in uno dei due formati:
{"status":"tool_requests","reason":"...","tools":[{"name":"pytest_quiet","arguments":{}}]}
oppure
{"status":"final","answer":"risposta finale in italiano"}

Strumenti consentiti:
- pytest_quiet: esegue pytest senza cache e senza bytecode, timeout 180 s.
- git_status
- git_recent_log, arguments: {"count": 10}
- git_diff_stat
- git_count_ahead
- inspect_file_bytes, arguments: {"path":"requirements.txt","byte_count":256}
- read_file_excerpt, arguments: {"path":"README.md","max_chars":5000}
- list_project_files, arguments: {"max_depth":2}

Regole:
1. Richiedi solo strumenti necessari alla domanda.
2. Massimo 6 strumenti per turno.
3. Non richiedere modifiche, installazioni, push, commit o comandi arbitrari.
4. Non ripetere uno strumento gia eseguito salvo motivazione concreta.
5. Quando i dati sono sufficienti, restituisci status final con una risposta completa e concreta.
6. Distingui chiaramente cio che e stato osservato da cio che e raccomandato.
7. Se una modifica e il prossimo passo, proponi un unico piano delimitato da approvare una sola volta.
"""

    for round_index in range(1, MAX_TOOL_ROUNDS + 1):
        input_text = (
            "RICHIESTA UTENTE:\n" + user_request +
            "\n\nACTIVE DISCOVERY:\n" + compact(discovery) +
            "\n\nDELIBERAZIONE MAGI INIZIALE:\n" + compact(initial_magi) +
            "\n\nRISULTATI STRUMENTI GIA ESEGUITI:\n" + compact(tool_history)
        )
        raw = openai_text(api_key, model, planner_instructions, input_text, timeout)
        try:
            decision = parse_json_object(raw)
        except Exception:
            # Fail-safe: use the model text as the final answer rather than looping forever.
            return raw, tool_history, round_index

        status = str(decision.get("status", "")).lower()
        if status == "final":
            answer = str(decision.get("answer", "")).strip()
            if answer:
                return answer, tool_history, round_index
            return "Il cervello non ha prodotto una risposta finale valida.", tool_history, round_index

        if status != "tool_requests":
            return raw, tool_history, round_index

        tools = decision.get("tools") if isinstance(decision.get("tools"), list) else []
        if not tools:
            return "Non sono stati richiesti strumenti validi e non e stata prodotta una risposta finale.", tool_history, round_index

        round_results: list[dict] = []
        for tool_request in tools[:MAX_TOOLS_PER_ROUND]:
            if not isinstance(tool_request, dict):
                continue
            signature = json.dumps(tool_request, sort_keys=True, ensure_ascii=False)
            if any(item.get("signature") == signature for item in tool_history):
                round_results.append({"signature": signature, "name": tool_request.get("name"), "exit_code": 125, "output": "Richiesta duplicata ignorata."})
                continue
            executed = execute_safe_tool(repo, tool_request)
            executed["round"] = round_index
            executed["signature"] = signature
            round_results.append(executed)
        tool_history.extend(round_results)

    final_instructions = """Sei il cervello finale di Pixel Bot. Produci una risposta in italiano usando soltanto i dati reali forniti. Spiega sinteticamente cosa e stato verificato, i risultati e il prossimo intervento prudente. Non chiedere conferma per ulteriori letture o test sicuri. Se serve una modifica, proponi un unico piano delimitato da approvare una volta sola. Non inventare risultati."""
    final_input = (
        "RICHIESTA:\n" + user_request +
        "\n\nDISCOVERY:\n" + compact(discovery) +
        "\n\nMAGI:\n" + compact(initial_magi) +
        "\n\nRISULTATI TOOL LOOP:\n" + compact(tool_history)
    )
    return openai_text(api_key, model, final_instructions, final_input, timeout), tool_history, MAX_TOOL_ROUNDS


def magi_summary(magi: dict, report_path: Path, discovery_path: Path, tool_history: list[dict], rounds: int, final_report: Path | None) -> str:
    status = magi.get("status", "sconosciuto")
    action = magi.get("recommended_action", "")
    review = "SI" if magi.get("requires_creator_review") else "NO"
    lines = [
        "Active Discovery: completata automaticamente",
        f"Discovery report: {discovery_path}",
        f"Autonomous Tool Loop: {rounds} turno/i, {len(tool_history)} strumento/i eseguito/i",
        f"Stato MAGI iniziale: {status}",
        f"Revisione del creatore richiesta: {review}",
    ]
    if action:
        lines.append(f"Azione consigliata iniziale: {action}")
    for item in magi.get("opinions", []) or []:
        role = str(item.get("role", "magi")).capitalize()
        lines.append(f"{role} [{item.get('status', '')}]: {item.get('summary', '')}")
    lines.append(f"Report MAGI iniziale: {report_path}")
    if final_report:
        lines.append(f"Report MAGI finale: {final_report}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--request-file", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    request_file = Path(args.request_file)
    user_request = request_file.read_text(encoding="utf-8-sig").strip()
    if not user_request:
        raise SystemExit("Richiesta vuota.")

    load_dotenv(repo / ".env")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        emit("PIXELBOT_ERROR_B64", "OPENAI_API_KEY non presente nel file .env del progetto.")
        return 2
    model = os.getenv("OPENAI_MODEL", "gpt-5").strip() or "gpt-5"
    try:
        timeout = int(os.getenv("PIXEL_BOT_AI_TIMEOUT", "120"))
    except ValueError:
        timeout = 120

    try:
        discovery, discovery_path = discover_project_context(repo, user_request)
        initial_magi, initial_report = run_magi(repo, user_request, discovery, "initial")
        answer, tool_history, rounds = autonomous_tool_loop(
            api_key, model, timeout, repo, user_request, discovery, initial_magi
        )

        final_context = {
            "active_discovery": discovery,
            "autonomous_tool_results": tool_history,
            "candidate_answer": answer,
        }
        final_magi, final_report = run_magi(repo, user_request, final_context, "final")

        # Save a complete audit report of the loop.
        loop_dir = repo / "workspace" / "autonomous-tool-loop"
        loop_dir.mkdir(parents=True, exist_ok=True)
        loop_report = loop_dir / f"loop-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
        loop_report.write_text(json.dumps({
            "request": user_request,
            "rounds": rounds,
            "tool_history": tool_history,
            "initial_magi": initial_magi,
            "final_magi": final_magi,
            "answer": answer,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        summary = magi_summary(initial_magi, initial_report, discovery_path, tool_history, rounds, final_report)
        summary += f"\nLoop report: {loop_report}"
        emit("PIXELBOT_MAGI_B64", summary)
        emit("PIXELBOT_ANSWER_B64", answer)
        return 0
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        emit("PIXELBOT_ERROR_B64", f"Errore OpenAI HTTP {exc.code}: {detail[:1200]}")
        return 3
    except Exception as exc:
        emit("PIXELBOT_ERROR_B64", f"Errore del cervello: {exc}")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class GateResult:
    status: str
    exit_code: int
    tests_passed: bool
    dirty_entries: list[str]
    blocking_entries: list[str]
    recommendation: str
    report_json: str
    report_txt: str


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=repo, text=True, capture_output=True, check=False
    )


def _python(repo: Path) -> Path:
    candidate = repo / ".venv" / "Scripts" / "python.exe"
    return candidate if candidate.exists() else Path("python")


def evaluate(repo: Path) -> GateResult:
    repo = repo.resolve()
    out_dir = repo / "workspace" / "auto-advance-gate"
    out_dir.mkdir(parents=True, exist_ok=True)

    pytest = _run(repo, str(_python(repo)), "-m", "pytest", "-q")
    tests_passed = pytest.returncode == 0

    status_cp = _run(repo, "git", "status", "--porcelain")
    dirty = [line for line in status_cp.stdout.splitlines() if line.strip()]

    blocking = []
    for entry in dirty:
        path = entry[3:].strip().strip('"') if len(entry) > 3 else entry
        if path.endswith((".bak", ".tmp", ".swp")):
            continue
        if path.startswith("workspace/") or path.startswith("workspace\\"):
            continue
        blocking.append(entry)

    if not tests_passed:
        status = "ROSSO"
        code = 1
        recommendation = "Correggere i test prima di applicare un nuovo aggiornamento."
    elif blocking:
        status = "ARANCIONE"
        code = 0
        recommendation = "Consolidare automaticamente i file di progetto prima del prossimo aggiornamento."
    else:
        status = "VERDE"
        code = 0
        recommendation = "Repository pronto: Pixel Bot puo proporre ed eseguire il prossimo aggiornamento sicuro."

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = out_dir / f"gate-{stamp}.json"
    txt_path = out_dir / f"gate-{stamp}.txt"

    result = GateResult(
        status=status,
        exit_code=code,
        tests_passed=tests_passed,
        dirty_entries=dirty,
        blocking_entries=blocking,
        recommendation=recommendation,
        report_json=str(json_path),
        report_txt=str(txt_path),
    )

    payload = asdict(result)
    payload["pytest_stdout"] = pytest.stdout
    payload["pytest_stderr"] = pytest.stderr
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "PB-031 AUTO-ADVANCE GATE",
        "========================",
        f"Stato: {status}",
        f"Codice uscita: {code}",
        f"Test superati: {'SI' if tests_passed else 'NO'}",
        f"Elementi working tree: {len(dirty)}",
        f"Elementi bloccanti: {len(blocking)}",
        "",
        "Raccomandazione:",
        recommendation,
    ]
    if blocking:
        lines += ["", "Elementi da consolidare:", *[f"- {x}" for x in blocking]]
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nReport JSON: {json_path}")
    print(f"Report TXT: {txt_path}")
    return result


if __name__ == "__main__":
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    raise SystemExit(evaluate(root).exit_code)

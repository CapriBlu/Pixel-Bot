from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


IGNORED_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "_stored",
    "Aggiornamenti Pixel Bot",
    "local-updates",
}


@dataclass(frozen=True)
class ModuleAudit:
    path: str
    lines: int
    code_lines: int
    classes: int
    functions: int
    imports: tuple[str, ...]
    syntax_error: str | None = None


@dataclass(frozen=True)
class ArchitectureReport:
    repository: str
    python_files: int
    total_lines: int
    code_lines: int
    classes: int
    functions: int
    packages: tuple[str, ...]
    largest_modules: tuple[ModuleAudit, ...]

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["largest_modules"] = [asdict(item) for item in self.largest_modules]
        return data


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if not _is_ignored(relative):
            yield path


def audit_module(path: Path, root: Path) -> ModuleAudit:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    code_lines = sum(1 for line in lines if line.strip() and not line.lstrip().startswith("#"))
    syntax_error: str | None = None
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        tree = ast.Module(body=[], type_ignores=[])
        syntax_error = f"{exc.msg} (line {exc.lineno})"

    imports: set[str] = set()
    classes = 0
    functions = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
        elif isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])

    return ModuleAudit(
        path=path.relative_to(root).as_posix(),
        lines=len(lines),
        code_lines=code_lines,
        classes=classes,
        functions=functions,
        imports=tuple(sorted(imports)),
        syntax_error=syntax_error,
    )


def build_report(repository: Path) -> ArchitectureReport:
    repository = repository.resolve()
    modules = [audit_module(path, repository) for path in iter_python_files(repository)]
    packages = sorted(
        {
            str(Path(module.path).parent).replace("\\", "/")
            for module in modules
            if Path(module.path).name == "__init__.py"
        }
    )
    largest = tuple(sorted(modules, key=lambda item: (-item.code_lines, item.path))[:15])
    return ArchitectureReport(
        repository=str(repository),
        python_files=len(modules),
        total_lines=sum(item.lines for item in modules),
        code_lines=sum(item.code_lines for item in modules),
        classes=sum(item.classes for item in modules),
        functions=sum(item.functions for item in modules),
        packages=tuple(packages),
        largest_modules=largest,
    )


def write_report(repository: Path, output: Path) -> ArchitectureReport:
    report = build_report(repository)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate the PB-054 repository architecture audit.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("workspace/pb054-architecture-audit.json"))
    args = parser.parse_args()
    report = write_report(args.repo, args.output)
    print(f"PB-054 audit complete: {report.python_files} Python files, {report.code_lines} code lines")
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# PB-054 - Architecture Audit

PB-054 adds a deterministic, read-only architecture scanner for the current repository layout.

## Purpose

- count Python files and source lines;
- identify packages, classes and functions;
- list the largest modules;
- produce a machine-readable JSON snapshot;
- ignore Git, virtual environments, caches and historical update archives.

## Run

```powershell
.\.venv\Scripts\python.exe -m pixel_bot.developer.architecture_audit
```

Default report:

```text
workspace/pb054-architecture-audit.json
```

This update does not move existing files and does not change runtime behavior.

from __future__ import annotations

import json

import pytest

from pixel_bot.magi.cli import main


def test_cli_creates_report_and_individual_memories(tmp_path, capsys):
    report = tmp_path / "magi.json"
    memory_dir = tmp_path / "memory"

    result = main(
        [
            "--goal",
            "Scegliere un micro-intervento con test e criterio misurabile",
            "--context",
            "Fondamenta prima delle funzionalità.",
            "--dry-run",
            "--report",
            str(report),
            "--memory-dir",
            str(memory_dir),
        ]
    )

    assert result == 0
    assert report.exists()
    for role in ("melchior", "balthasar", "caspar"):
        assert (memory_dir / f"{role}.jsonl").exists()

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert {item["role"] for item in payload["opinions"]} == {
        "melchior",
        "balthasar",
        "caspar",
    }
    console = json.loads(capsys.readouterr().out)
    assert console["memory_written"] is True


def test_cli_can_skip_memory_write(tmp_path):
    memory_dir = tmp_path / "memory"
    main(
        [
            "--goal",
            "Valutare un test misurabile",
            "--dry-run",
            "--report",
            str(tmp_path / "magi.json"),
            "--memory-dir",
            str(memory_dir),
            "--no-memory-write",
        ]
    )

    assert not memory_dir.exists()


def test_cli_refuses_non_dry_run(tmp_path):
    with pytest.raises(SystemExit, match="esclusivamente --dry-run"):
        main(
            [
                "--goal",
                "Modificare il progetto",
                "--report",
                str(tmp_path / "magi.json"),
            ]
        )

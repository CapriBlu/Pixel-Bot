from pathlib import Path

from pixel_bot.developer.architecture_audit import build_report, write_report


def test_build_report_ignores_generated_and_historical_directories(tmp_path: Path) -> None:
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "pkg" / "module.py").write_text(
        "import json\n\nclass Example:\n    pass\n\ndef run():\n    return json.dumps({})\n",
        encoding="utf-8",
    )
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ignored.py").write_text("raise RuntimeError\n", encoding="utf-8")

    report = build_report(tmp_path)

    assert report.python_files == 2
    assert report.classes == 1
    assert report.functions == 1
    assert "src/pkg" in report.packages
    assert report.largest_modules[0].path == "src/pkg/module.py"


def test_write_report_creates_json(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    output = tmp_path / "workspace" / "audit.json"

    report = write_report(tmp_path, output)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert '"python_files": 1' in text
    assert report.functions == 1

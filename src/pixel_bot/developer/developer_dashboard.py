from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


class DeveloperDashboard:
    """Genera una dashboard HTML locale e portabile da journal, health e analisi."""

    def render(self, output_path: Path, events: list[dict[str, Any]], health: dict[str, Any], analysis: dict[str, Any]) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rows = "".join(
            f"<tr><td>{html.escape(str(e.get('sequence','')))}</td><td>{html.escape(str(e.get('timestamp','')))}</td><td>{html.escape(str(e.get('type','')))}</td><td><pre>{html.escape(json.dumps(e.get('payload',{}), ensure_ascii=False))}</pre></td></tr>"
            for e in reversed(events)
        )
        page = f"""<!doctype html><html lang='it'><head><meta charset='utf-8'><title>Pixel-Bot Foundation Dashboard</title>
<style>body{{font-family:Segoe UI,Arial;margin:24px;background:#111827;color:#e5e7eb}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}}.card{{background:#1f2937;padding:16px;border-radius:12px}}table{{width:100%;border-collapse:collapse;margin-top:20px}}td,th{{border-bottom:1px solid #374151;padding:8px;text-align:left;vertical-align:top}}pre{{white-space:pre-wrap;margin:0}}</style></head><body>
<h1>Pixel-Bot Foundation Dashboard</h1><div class='grid'><div class='card'><h2>Health</h2><pre>{html.escape(json.dumps(health, ensure_ascii=False, indent=2))}</pre></div><div class='card'><h2>Self Analysis</h2><pre>{html.escape(json.dumps(analysis, ensure_ascii=False, indent=2))}</pre></div></div>
<h2>Event History</h2><table><thead><tr><th>#</th><th>Timestamp</th><th>Evento</th><th>Payload</th></tr></thead><tbody>{rows}</tbody></table></body></html>"""
        output_path.write_text(page, encoding="utf-8")
        return output_path

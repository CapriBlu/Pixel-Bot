from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "pixelbot_brain_bridge.py"
spec = importlib.util.spec_from_file_location("pixelbot_brain_bridge_pb0331", MODULE_PATH)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def test_extract_numbered_checklist_only():
    request = """Completa la validazione.\n1. verifica .gitattributes\n2) controlla il loop\nTesto normale\n3: genera report"""
    assert bridge.extract_request_checklist(request) == [
        {"id": "1", "text": "verifica .gitattributes"},
        {"id": "2", "text": "controlla il loop"},
        {"id": "3", "text": "genera report"},
    ]


def test_completed_requires_real_successful_evidence():
    checklist = [{"id": "1", "text": "verifica"}]
    reported = [{
        "item_id": "1",
        "status": "completed",
        "summary": "ok",
        "evidence_signatures": ["sig-1"],
    }]
    valid, errors = bridge.validate_checklist_completion(
        checklist,
        reported,
        [{"signature": "sig-1", "exit_code": 0}],
    )
    assert valid is True
    assert errors == []


def test_completed_without_tool_evidence_is_rejected():
    checklist = [{"id": "1", "text": "verifica"}]
    reported = [{
        "item_id": "1",
        "status": "completed",
        "summary": "ok",
        "evidence_signatures": [],
    }]
    valid, errors = bridge.validate_checklist_completion(checklist, reported, [])
    assert valid is False
    assert any("senza evidenza" in error for error in errors)


def test_missing_mandatory_item_is_rejected():
    checklist = [
        {"id": "1", "text": "prima"},
        {"id": "2", "text": "seconda"},
    ]
    reported = [{
        "item_id": "1",
        "status": "unavailable",
        "summary": "strumento non disponibile",
        "evidence_signatures": [],
    }]
    valid, errors = bridge.validate_checklist_completion(checklist, reported, [])
    assert valid is False
    assert "punto 2 senza esito" in errors


def test_unavailable_requires_reason():
    checklist = [{"id": "1", "text": "verifica"}]
    reported = [{
        "item_id": "1",
        "status": "unavailable",
        "summary": "",
        "evidence_signatures": [],
    }]
    valid, errors = bridge.validate_checklist_completion(checklist, reported, [])
    assert valid is False
    assert any("senza motivazione" in error for error in errors)

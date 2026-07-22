from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

from pixel_bot.developer import openai_state_bridge as bridge_module


class FakeCollector:
    def __init__(self, root):
        self.root = root

    def collect(self, goal):
        return {"goal": goal, "root": str(self.root)}


class FakeRegistry:
    schemas = [
        {
            "type": "function",
            "name": "read_file",
            "description": "Read a safe file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        }
    ]

    def __init__(self):
        self.calls = []

    def execute(self, name, arguments):
        self.calls.append((name, arguments))
        return {"ok": True, "content": "hello"}


class FakeResponses:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("No fake response left")
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.responses = FakeResponses(responses)


def _response(response_id, output, text=""):
    return SimpleNamespace(
        id=response_id,
        output=output,
        output_text=text,
        _request_id=f"req-{response_id}",
    )


def _build_bridge(tmp_path, registry):
    bridge = bridge_module.OpenAIStateBridge.__new__(
        bridge_module.OpenAIStateBridge
    )
    bridge.root = tmp_path
    bridge.model = "test-model"
    bridge.registry = registry
    return bridge


def test_multiround_function_call_flow(monkeypatch, tmp_path):
    registry = FakeRegistry()
    function_call = SimpleNamespace(
        type="function_call",
        name="read_file",
        arguments=json.dumps({"path": "README.md"}),
        call_id="call-1",
    )
    client = FakeClient(
        [
            _response("resp-1", [function_call]),
            _response("resp-2", [], text="VERDE"),
        ]
    )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(bridge_module, "StateCollector", FakeCollector)
    monkeypatch.setattr(bridge_module, "sanitize_state", lambda value: value)
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=lambda: client),
    )

    bridge = _build_bridge(tmp_path, registry)
    result = bridge.analyze("Inspect repository", max_rounds=3)

    assert result["status"] == "completed"
    assert result["text"] == "VERDE"
    assert result["rounds"] == 1
    assert registry.calls == [("read_file", {"path": "README.md"})]
    assert len(client.responses.calls) == 2

    second_input = client.responses.calls[1]["input"]
    assert function_call in second_input
    tool_outputs = [
        item
        for item in second_input
        if isinstance(item, dict)
        and item.get("type") == "function_call_output"
    ]
    assert len(tool_outputs) == 1
    assert tool_outputs[0]["call_id"] == "call-1"
    assert json.loads(tool_outputs[0]["output"])["ok"] is True


def test_tool_exception_is_returned_to_model(monkeypatch, tmp_path):
    class FailingRegistry(FakeRegistry):
        def execute(self, name, arguments):
            raise RuntimeError("tool failed")

    registry = FailingRegistry()
    function_call = SimpleNamespace(
        type="function_call",
        name="read_file",
        arguments="{}",
        call_id="call-error",
    )
    client = FakeClient(
        [
            _response("resp-1", [function_call]),
            _response("resp-2", [], text="ARANCIONE"),
        ]
    )

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(bridge_module, "StateCollector", FakeCollector)
    monkeypatch.setattr(bridge_module, "sanitize_state", lambda value: value)
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=lambda: client),
    )

    bridge = _build_bridge(tmp_path, registry)
    result = bridge.analyze("Inspect repository", max_rounds=3)

    assert result["status"] == "completed"
    output_item = client.responses.calls[1]["input"][-1]
    payload = json.loads(output_item["output"])
    assert payload == {
        "ok": False,
        "error": "tool failed",
        "tool": "read_file",
    }


def test_max_rounds_returns_bounded(monkeypatch, tmp_path):
    registry = FakeRegistry()
    responses = []
    for index in range(2):
        responses.append(
            _response(
                f"resp-{index}",
                [
                    SimpleNamespace(
                        type="function_call",
                        name="read_file",
                        arguments="{}",
                        call_id=f"call-{index}",
                    )
                ],
                text="still working",
            )
        )
    client = FakeClient(responses)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(bridge_module, "StateCollector", FakeCollector)
    monkeypatch.setattr(bridge_module, "sanitize_state", lambda value: value)
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=lambda: client),
    )

    bridge = _build_bridge(tmp_path, registry)
    result = bridge.analyze("Inspect repository", max_rounds=2)

    assert result["status"] == "bounded"
    assert result["rounds"] == 2
    assert len(client.responses.calls) == 2


def test_missing_api_key_fails_fast(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=lambda: None),
    )

    bridge = _build_bridge(tmp_path, FakeRegistry())

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY non configurata"):
        bridge.analyze("Inspect repository")

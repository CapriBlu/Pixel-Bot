import json
from pathlib import Path

from pixel_bot.agent.ai_client import AIClientConfig
from pixel_bot.developer.ai_provider import DeveloperAIProvider
from pixel_bot.developer.models import DevelopmentPlan, DevelopmentTask, RepositorySnapshot


def test_config_uses_openai_responses_when_key_is_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("PIXEL_BOT_AI_ENDPOINT", raising=False)
    monkeypatch.delenv("PIXEL_BOT_DRY_RUN", raising=False)

    config = AIClientConfig.from_environment()

    assert config.provider == "openai"
    assert config.endpoint == "https://api.openai.com/v1/responses"
    assert config.token == "test-key"


def test_openai_adapter_builds_schema_request_and_parses_changes(tmp_path: Path):
    captured = {}

    def transport(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(
                                {
                                    "changes": [
                                        {
                                            "path": "docs/STATUS.md",
                                            "content": "# Status\\n",
                                            "reason": "Aggiorna lo stato.",
                                        }
                                    ]
                                }
                            ),
                        }
                    ],
                }
            ]
        }

    config = AIClientConfig(
        endpoint="https://api.openai.com/v1/responses",
        token="test-key",
        model="gpt-5-mini",
        provider="openai",
        max_requests_per_task=1,
    )
    provider = DeveloperAIProvider(tmp_path, config, transport=transport)
    task = DevelopmentTask(
        "PB-012",
        "Status",
        "Aggiorna lo stato",
        allowed_paths=["docs"],
    )
    snapshot = RepositorySnapshot(tmp_path, [], [], [], [])
    plan = DevelopmentPlan(task, [], [])

    changes = provider(task, snapshot, plan)

    assert changes[0].path == "docs/STATUS.md"
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["payload"]["model"] == "gpt-5-mini"
    assert captured["payload"]["text"]["format"]["type"] == "json_schema"
    assert captured["payload"]["text"]["format"]["strict"] is True
    assert provider.budget.requests_used == 1

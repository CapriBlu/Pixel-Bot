from pixel_bot.developer.state_sanitizer import sanitize_state


def test_redacts_secret_keys_and_api_keys():
    value = {"token": "abc", "text": "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456"}
    cleaned = sanitize_state(value)
    assert cleaned["token"] == "[REDACTED]"
    assert "sk-" not in cleaned["text"]

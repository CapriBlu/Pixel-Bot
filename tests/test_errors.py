from pixel_bot.core.errors import ScreenCaptureError


def test_pixelbot_error_is_structured():
    error = ScreenCaptureError("errore", context={"monitor": 3})

    assert error.recoverable is True
    assert error.to_dict() == {
        "type": "ScreenCaptureError",
        "code": "screen_capture_error",
        "message": "errore",
        "recoverable": True,
        "context": {"monitor": 3},
    }

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from pixel_bot.core.errors import ScreenCaptureError
from pixel_bot.vision.screen_capture import CaptureRegion, capture_screen, capture_screen_result


class FakeCapture:
    monitors = [
        {"left": 0, "top": 0, "width": 200, "height": 100},
        {"left": 0, "top": 0, "width": 100, "height": 50},
    ]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def grab(self, target):
        return SimpleNamespace(
            rgb=b"rgb",
            size=SimpleNamespace(width=target["width"], height=target["height"]),
        )


def test_capture_screen_preserves_path_api(tmp_path):
    with patch("pixel_bot.vision.screen_capture.mss.mss", return_value=FakeCapture()), patch(
        "pixel_bot.vision.screen_capture.mss.tools.to_png"
    ) as to_png:
        path = capture_screen(monitor=1, output_dir=tmp_path, filename="test.png")

    assert path == tmp_path / "test.png"
    to_png.assert_called_once()


def test_capture_region_returns_metadata(tmp_path):
    region = CaptureRegion(left=10, top=20, width=30, height=40)
    with patch("pixel_bot.vision.screen_capture.mss.mss", return_value=FakeCapture()), patch(
        "pixel_bot.vision.screen_capture.mss.tools.to_png"
    ):
        result = capture_screen_result(region=region, output_dir=tmp_path)

    assert result.monitor is None
    assert result.region == region
    assert (result.width, result.height) == (30, 40)


def test_invalid_monitor_is_structured_error(tmp_path):
    with patch("pixel_bot.vision.screen_capture.mss.mss", return_value=FakeCapture()):
        with pytest.raises(ScreenCaptureError) as caught:
            capture_screen(monitor=9, output_dir=tmp_path)

    assert caught.value.context["available_monitors"] == 1

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mss
import mss.tools

from pixel_bot.config import get_settings
from pixel_bot.core.errors import ScreenCaptureError
from pixel_bot.core.logger import get_logger, log_event

logger = get_logger(__name__)


@dataclass(slots=True, frozen=True)
class CaptureRegion:
    left: int
    top: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("La regione deve avere larghezza e altezza positive.")

    def to_mss(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass(slots=True, frozen=True)
class ScreenCaptureResult:
    path: Path
    monitor: int | None
    region: CaptureRegion | None
    width: int
    height: int
    captured_at: str


def _resolve_target(
    capture: Any,
    monitor: int,
    region: CaptureRegion | None,
) -> dict[str, int]:
    if region is not None:
        return region.to_mss()
    if monitor <= 0 or monitor >= len(capture.monitors):
        available = max(0, len(capture.monitors) - 1)
        raise ScreenCaptureError(
            f"Monitor {monitor} non disponibile. Monitor disponibili: {available}.",
            context={"monitor": monitor, "available_monitors": available},
        )
    return capture.monitors[monitor]


def capture_screen_result(
    *,
    monitor: int | None = None,
    region: CaptureRegion | None = None,
    output_dir: str | Path | None = None,
    filename: str | None = None,
) -> ScreenCaptureResult:
    settings = get_settings()
    selected_monitor = monitor if monitor is not None else settings.default_monitor
    directory = Path(output_dir) if output_dir is not None else settings.screenshots_dir
    directory.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    safe_filename = filename or now.strftime("screen_%Y%m%d_%H%M%S_%f.png")
    if Path(safe_filename).name != safe_filename or not safe_filename.lower().endswith(".png"):
        raise ValueError("Il nome del file deve essere un semplice nome PNG.")
    output_path = directory / safe_filename

    try:
        with mss.mss() as capture:
            target = _resolve_target(capture, selected_monitor, region)
            screenshot = capture.grab(target)
            mss.tools.to_png(
                screenshot.rgb,
                screenshot.size,
                output=str(output_path),
            )
    except ScreenCaptureError:
        raise
    except Exception as exc:
        raise ScreenCaptureError(
            "Acquisizione dello schermo non riuscita.",
            context={"monitor": selected_monitor, "output": str(output_path)},
        ) from exc

    result = ScreenCaptureResult(
        path=output_path,
        monitor=None if region is not None else selected_monitor,
        region=region,
        width=int(screenshot.size.width),
        height=int(screenshot.size.height),
        captured_at=now.isoformat(),
    )
    log_event(
        logger,
        "screen_captured",
        path=str(result.path),
        monitor=result.monitor,
        width=result.width,
        height=result.height,
    )
    return result


def capture_screen(
    monitor: int | None = None,
    *,
    region: CaptureRegion | None = None,
    output_dir: str | Path | None = None,
    filename: str | None = None,
) -> Path:
    """Capture a screen and return its path, preserving the original public API."""
    return capture_screen_result(
        monitor=monitor,
        region=region,
        output_dir=output_dir,
        filename=filename,
    ).path

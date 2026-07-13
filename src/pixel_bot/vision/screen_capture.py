from datetime import datetime
from pathlib import Path

import mss
import mss.tools

SCREENSHOTS_DIR = Path("screenshots")


def capture_screen():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = datetime.now().strftime("screen_%Y%m%d_%H%M%S.png")
    output_path = SCREENSHOTS_DIR / filename

    with mss.mss() as capture:
        monitor = capture.monitors[1]
        screenshot = capture.grab(monitor)

        mss.tools.to_png(
            screenshot.rgb,
            screenshot.size,
            output=str(output_path),
        )

    return output_path

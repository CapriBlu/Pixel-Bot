from pathlib import Path
import logging


LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOGS_DIR / "pixel_bot.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

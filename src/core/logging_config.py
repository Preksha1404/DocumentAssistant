import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# LOG DIRECTORY
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

# FORMAT
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# HANDLERS
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
    encoding="utf-8",
)

file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# ROOT LOGGER
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler],
)
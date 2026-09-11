"""Timestamped console+file diagnostic logging, shared by every run_*.py script."""
import logging
import sys
import time

from .config import LOG_DIR


def setup_logging(run_name: str) -> logging.Logger:
    """Configure the 'snntopo' logger to stream to stdout AND a timestamped file
    under results/logs/. Call once per script entry point."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%S")
    log_path = LOG_DIR / f"{run_name}_{ts}.log"

    logger = logging.getLogger("snntopo")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    logger.info(f"=== {run_name} — logging to {log_path.relative_to(LOG_DIR.parent.parent)} ===")
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("snntopo")

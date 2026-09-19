"""Timestamped console+file logging under the 'snntopo' logger."""
import logging
import sys
import time
from pathlib import Path


def setup_logging(run_name: str, log_dir) -> logging.Logger:
    """Stream the 'snntopo' logger to stdout and to <log_dir>/<run_name>_<ts>.log.
    Call once per entry point."""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{run_name}_{time.strftime('%Y%m%dT%H%M%S')}.log"

    logger = logging.getLogger("snntopo")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(log_path)):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.info(f"=== {run_name} — logging to {log_path} ===")
    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("snntopo")

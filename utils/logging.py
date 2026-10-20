import logging
from pathlib import Path

from utils.io import ensure_parent


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def configure_file_logger(name: str, path: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False

    target_path = str(Path(path))
    ensure_parent(target_path)

    for handler in list(logger.handlers):
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == Path(target_path):
            handler.setLevel(getattr(logging, level.upper(), logging.INFO))
            return logger

    file_handler = logging.FileHandler(target_path, encoding="utf-8")
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(file_handler)
    return logger

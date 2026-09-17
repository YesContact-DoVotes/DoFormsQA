import sys
import logging
from pathlib import Path
from loguru import logger
from backend.app.config import settings


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    Intercepts standard logging messages and redirects them to loguru.
    """
    def emit(self, record: logging.LogRecord):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """
    Configures loguru as the master logger with colorized console output
    and file persistence. Intercepts standard library and uvicorn logging.
    """
    # Create logs directory
    logs_dir = settings.STORAGE_PATH / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "qa_agent.log"

    # Remove all existing handlers
    logger.remove()

    # 1. Console Handler (Rich, colorized, timestamped)
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO",
        colorize=True,
        enqueue=True,
    )

    # 2. File Handler (Rotating log file)
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        encoding="utf-8",
    )

    # Intercept standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    for _log_name in [
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
        "playwright",
        "sqlalchemy",
        "aiosqlite"
    ]:
        _logger = logging.getLogger(_log_name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    logger.info("Loguru logging configured successfully. Log file: {}", log_file)

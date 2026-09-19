import json
import logging
from typing import Any

from src.config.settings import LOG_DIR, LOG_FILE


def _safe_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, sort_keys=True, default=str)
    return str(value)


class ContextFilter(logging.Filter):
    """Attach default structured metadata to every record."""

    def __init__(self, default_context: dict[str, Any] | None = None):
        super().__init__()
        self.default_context = default_context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        context = {
            "run_id": getattr(record, "run_id", None) or self.default_context.get("run_id"),
            "stage": getattr(record, "stage", None) or self.default_context.get("stage"),
            "coin_id": getattr(record, "coin_id", None) or self.default_context.get("coin_id"),
            "task": getattr(record, "task", None) or self.default_context.get("task"),
        }
        context = {key: value for key, value in context.items() if value is not None}

        for key, value in context.items():
            setattr(record, key, value)

        ordered = []
        for key in ("run_id", "stage", "coin_id", "task"):
            if key in context:
                ordered.append(f"{key}={_safe_value(context[key])}")

        message = record.getMessage()
        if ordered:
            record.msg = " ".join(ordered) + f" message={message}"
            # clear args to avoid formatting against previous placeholders
            record.args = ()
            record.message = record.getMessage()
        return True


def get_logger(name: str, **context: Any) -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = True

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    filtered_context = {key: value for key, value in context.items() if value is not None}
    context_filter = next((flt for flt in logger.filters if isinstance(flt, ContextFilter)), None)
    if context_filter is None:
        context_filter = ContextFilter(filtered_context)
        logger.addFilter(context_filter)
    context_filter.default_context = filtered_context
    logger._default_context = filtered_context

    return logger

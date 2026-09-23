"""Traceback logging that redacts configured credentials before emission."""

from __future__ import annotations

import re
import traceback
from logging import Logger

from backend.core.config import settings


def _redact(text: str) -> str:
    for value in (
        settings.database_url,
        settings.jwt_secret_key,
        settings.bootstrap_admin_password,
    ):
        if value:
            text = text.replace(str(value), "[REDACTED]")
    return re.sub(
        r"(?i)(postgres(?:ql)?(?:\+[^:]+)?://[^:\s]+:)[^@\s]+@",
        r"\1[REDACTED]@",
        text,
    )


def log_exception(logger: Logger, message: str, exc: BaseException) -> None:
    """Log a useful traceback while keeping configured secrets out of logs."""
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error("%s\n%s", message, _redact(details))

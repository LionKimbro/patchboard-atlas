"""
Structured log buffer for Patchboard Atlas.

Append-only runtime log rendered by the Console window.
"""

from datetime import datetime, timezone


g_log = []

_level_flags = {
    "i": "info",
    "w": "warning",
    "e": "error",
}


def log(category, message, flags="i"):
    """
    Append a log record to g_log.

    flags: "i" info, "w" warning, "e" error (mutually exclusive).
    """
    level = _level_flags[flags]
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "category": category,
        "message": message,
    }
    g_log.append(record)


def attach_context(context_obj):
    """
    Merge context dict into the last record in g_log.
    """
    g_log[-1]["context"] = context_obj


def clear_log():
    """Clear the log buffer."""
    g_log.clear()

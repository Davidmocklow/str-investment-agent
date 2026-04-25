"""
Alert history — persists fired alert IDs to a JSON file so the same alert
is never delivered twice. Marks re-seen alerts as is_new=False.
"""

from __future__ import annotations

import json
import os
from .models import Alert

_DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "alert_history.json"
)


def _load(path: str) -> dict[str, str]:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(history: dict[str, str], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def deduplicate(alerts: list[Alert], path: str = _DEFAULT_PATH) -> list[Alert]:
    """
    Marks alerts as is_new=False if their alert_id is already in history.
    Does NOT write to history — call commit() after delivery to persist.
    """
    history = _load(path)
    for alert in alerts:
        if alert.alert_id in history:
            alert.is_new = False
    return alerts


def commit(alerts: list[Alert], path: str = _DEFAULT_PATH) -> None:
    """Saves newly fired alert IDs to history so they won't re-fire."""
    history = _load(path)
    for alert in alerts:
        if alert.is_new:
            history[alert.alert_id] = alert.triggered_at
    _save(history, path)


def clear_history(path: str = _DEFAULT_PATH) -> None:
    """Reset history — useful for testing."""
    _save({}, path)


def history_count(path: str = _DEFAULT_PATH) -> int:
    return len(_load(path))

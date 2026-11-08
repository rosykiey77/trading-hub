"""Helpers shared by bot adapters."""
import sqlite3
from datetime import datetime, timezone


def ro_connect(path: str) -> sqlite3.Connection:
    """Read-only connection; raises if the file is missing (mode=ro never creates it)."""
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=2)
    c.row_factory = sqlite3.Row
    return c


def to_ts(v) -> float | None:
    """Epoch seconds from int/float or ISO-8601 string."""
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).timestamp()


def iso(ts) -> str | None:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat() if ts else None


def worst(*healths: str) -> str:
    order = ["green", "yellow", "red"]
    return max(healths, key=order.index)

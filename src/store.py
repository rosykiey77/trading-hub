"""Hub-owned SQLite: equity snapshots and control-action log."""
import sqlite3
import time
from pathlib import Path

RANGES = {"24h": 86400, "7d": 7 * 86400, "30d": 30 * 86400, "all": None}


def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE IF NOT EXISTS equity(t INTEGER, bot TEXT, equity REAL, PRIMARY KEY(t, bot))")
    c.execute("CREATE TABLE IF NOT EXISTS actions(t INTEGER, action TEXT, target TEXT, ok INTEGER, message TEXT)")
    return c


def add_equity(path: str, values: dict, t: int | None = None) -> None:
    t = t or int(time.time())
    with connect(path) as c:
        c.executemany("INSERT OR REPLACE INTO equity VALUES (?,?,?)",
                      [(t, bot, eq) for bot, eq in values.items() if eq is not None])


def equity(path: str, bot: str, rng: str) -> list[dict]:
    span = RANGES[rng]
    since = int(time.time()) - span if span else 0
    with connect(path) as c:
        rows = c.execute("SELECT t, equity FROM equity WHERE bot=? AND t>=? ORDER BY t", (bot, since)).fetchall()
    return [{"t": t, "equity": e} for t, e in rows]


def log_action(path: str, action: str, target: str, ok: bool, message: str) -> None:
    with connect(path) as c:
        c.execute("INSERT INTO actions VALUES (?,?,?,?,?)", (int(time.time()), action, target, int(ok), message))


def actions(path: str, limit: int = 50) -> list[dict]:
    with connect(path) as c:
        rows = c.execute("SELECT t, action, target, ok, message FROM actions ORDER BY rowid DESC LIMIT ?",
                         (limit,)).fetchall()
    return [{"t": r[0], "action": r[1], "target": r[2], "ok": bool(r[3]), "message": r[4]} for r in rows]

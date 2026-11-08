"""AssetTrade crypto futures. Reads the bot's own SQLite read-only (same data its API serves)."""
import json
import time

from .common import iso, ro_connect

STALE_S = 300  # bot itself treats 120 s without heartbeat as down; give the pill some slack


def fetch(s) -> dict:
    with ro_connect(s.futures_db) as c:
        state = {r["key"]: r["value"] for r in c.execute("SELECT key, value FROM state")}
        now = time.time()
        fills = c.execute("SELECT t, action, fee, pnl FROM fills WHERE mode='paper'").fetchall()
    c.close()
    get = lambda k, d=None: json.loads(state[k]) if k in state else d  # noqa: E731
    snap = get("snapshot", {})
    book = get("paper_book", {})
    marks = book.get("marks", {})
    hb = get("heartbeat")
    paused = bool(get("paused", False))

    def net(since=0):
        return round(sum((f["pnl"] or 0) if f["action"] == "close" else 0 for f in fills if f["t"] >= since)
                     - sum(f["fee"] or 0 for f in fills if f["t"] >= since), 4)

    positions = []
    for p in snap.get("positions", []):
        mark = marks.get(p["symbol"])
        long = str(p.get("side", "")).lower() in ("long", "buy", "1")
        roi = ((mark / p["entry"] - 1) * (1 if long else -1) * 100) if mark and p.get("entry") else None
        positions.append({
            "platform": "futures", "symbol": p["symbol"], "side": "LONG" if long else "SHORT",
            "size": p.get("qty"), "entry": p.get("entry"), "current": mark,
            "pnl": None, "roi_pct": round(roi, 2) if roi is not None else None,
            "sl": p.get("stop"), "tp": None, "opened_at": iso(p.get("opened_at")),
            "whale": None, "whale_win_rate": None, "stale": mark is None,
        })
    stale = not hb or now - hb > STALE_S
    return {
        "bot": "futures", "name": "AssetTrade Futures",
        "health": "yellow" if (stale or paused) else "green",
        "equity": snap.get("equity"), "cash": book.get("cash"),
        "realized_pnl_total": net(), "realized_pnl_24h": net(now - 86400),
        "open_positions": len(positions), "paused": paused,
        "updated_at": iso(hb), "error": "heartbeat stale" if stale else None,
        "positions": positions,
    }

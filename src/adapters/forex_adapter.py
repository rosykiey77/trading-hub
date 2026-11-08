"""Forex & Gold paper bot. Read-only SQLite."""
import os
import time

from .common import ro_connect, to_ts


def fetch(s) -> dict:
    c = ro_connect(s.forex_db)
    try:
        acct = c.execute("SELECT balance, daily_locked, updated_at FROM account WHERE id=1").fetchone()
        pos = c.execute("SELECT * FROM positions").fetchall()
        trades = c.execute("SELECT net_pnl, exit_time FROM trades").fetchall()
    finally:
        c.close()
    now = time.time()
    balance = acct["balance"] if acct else 0.0
    floating = sum(p["floating_pnl"] or 0 for p in pos)
    positions = [{
        "platform": "forex", "symbol": p["symbol"],
        "side": "LONG" if str(p["side"]).upper() in ("BUY", "LONG") else "SHORT",
        "size": p["lots"], "entry": p["entry_price"], "current": None,
        "pnl": p["floating_pnl"],
        "roi_pct": round(p["floating_pnl"] / p["initial_risk"] * 100, 2) if p["initial_risk"] else None,
        "sl": p["sl"], "tp": p["tp"], "opened_at": p["open_time"],
        "whale": None, "whale_win_rate": None, "stale": False,
    } for p in pos]
    stopped = os.path.exists(os.path.join(s.forex_dir, "STOP"))
    locked = bool(acct and acct["daily_locked"])
    return {
        "bot": "forex", "name": "Forex & Gold",
        "health": "yellow" if (stopped or locked) else "green",
        "equity": round(balance + floating, 2), "cash": balance,
        "realized_pnl_total": round(sum(t["net_pnl"] or 0 for t in trades), 2),
        "realized_pnl_24h": round(sum(t["net_pnl"] or 0 for t in trades
                                      if (to_ts(t["exit_time"]) or 0) >= now - 86400), 2),
        "open_positions": len(positions), "paused": stopped or locked,
        "updated_at": acct["updated_at"] if acct else None,
        "error": "STOP file present" if stopped else "daily loss lock" if locked else None,
        "positions": positions,
    }

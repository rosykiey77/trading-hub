"""PolyFollow Polymarket paper engine: portfolio JSON + tracker API health + Hermes job state (read-only)."""
import json
import os
import time

import httpx

from .common import iso, to_ts

STALE_S = 900


def _job_paused(s) -> bool | None:
    try:
        with open(s.hermes_jobs) as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    jobs = d if isinstance(d, list) else d.get("jobs", d)
    for j in (jobs if isinstance(jobs, list) else jobs.values()):
        if isinstance(j, dict) and j.get("id") == s.poly_cron_job:
            return not j.get("enabled", True) or j.get("state") == "paused"
    return None


def _api_ok(s) -> bool:
    try:
        r = httpx.get(f"{s.poly_api}/health", timeout=3)
        return r.status_code == 200 and r.json().get("status") == "healthy"
    except (httpx.HTTPError, ValueError):
        return False


def fetch(s) -> dict:
    with open(s.poly_portfolio) as f:
        pf = json.load(f)  # engine rewrites the file; a partial read raises and the bot shows red
    mtime = os.path.getmtime(s.poly_portfolio)
    now = time.time()
    positions, value = [], 0.0
    for p in pf.get("open_positions", []):
        cur = p.get("current_price") or p.get("entry_price") or 0
        val = (p.get("shares") or 0) * cur
        value += val
        positions.append({
            "platform": "polymarket", "symbol": p.get("market_title"), "side": p.get("outcome"),
            "size": p.get("shares"), "entry": p.get("entry_price"), "current": p.get("current_price"),
            "pnl": round(val - (p.get("cost_basis") or 0), 4), "roi_pct": p.get("unrealized_roi"),
            "sl": p.get("sl_target"), "tp": p.get("tp_target"), "opened_at": p.get("entry_time"),
            "whale": p.get("copy_trader"), "whale_win_rate": p.get("trader_win_rate"),
            "stale": bool(p.get("price_stale")),
        })
    try:  # journal has partial legs too; closed_positions only holds final legs
        with open(s.poly_journal) as f:
            legs = json.load(f)
    except (OSError, ValueError):
        legs = pf.get("closed_positions", [])
    pnl24 = sum(c.get("realized_pnl") or 0 for c in legs if (to_ts(c.get("exit_time")) or 0) >= now - 86400)
    paused = _job_paused(s)
    api_ok = _api_ok(s)
    stale = now - mtime > STALE_S
    health = "red" if not api_ok else "yellow" if (paused or stale) else "green"
    err = "tracker API down" if not api_ok else "portfolio not updated >15 min" if stale else None
    return {
        "bot": "polymarket", "name": "PolyFollow Polymarket",
        "health": health, "equity": round(pf.get("cash_balance", 0) + value, 4),
        "cash": pf.get("cash_balance"),
        "realized_pnl_total": round(pf.get("total_realized_pnl", 0), 4),
        "realized_pnl_24h": round(pnl24, 4),
        "open_positions": len(positions), "paused": bool(paused),
        "updated_at": iso(mtime), "error": err, "positions": positions,
    }

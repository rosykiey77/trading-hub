import hashlib
import json
import os

import pytest

from src.adapters import forex_adapter, futures_adapter, polyfollow_adapter, system_adapter


def digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_futures(settings):
    before = digest(settings.futures_db)
    s = futures_adapter.fetch(settings)
    assert s["equity"] == 1050.0 and s["health"] == "green" and s["open_positions"] == 1
    assert s["realized_pnl_total"] == 28.0  # 20 + 10 - fees 2
    assert s["realized_pnl_24h"] == 9.0
    p = s["positions"][0]
    assert p["side"] == "LONG" and p["roi_pct"] == 10.0 and p["sl"] == 90.0
    assert digest(settings.futures_db) == before  # read-only


def test_futures_stale_heartbeat(settings):
    import sqlite3
    c = sqlite3.connect(settings.futures_db)
    c.execute("UPDATE state SET value='1' WHERE key='heartbeat'"); c.commit(); c.close()
    assert futures_adapter.fetch(settings)["health"] == "yellow"


def test_futures_missing_db_raises(settings, tmp_path):
    settings.futures_db = str(tmp_path / "nope.db")
    with pytest.raises(Exception):
        futures_adapter.fetch(settings)
    assert not os.path.exists(settings.futures_db)  # mode=ro never creates the file


def test_polyfollow(settings):
    before = digest(settings.poly_portfolio)
    s = polyfollow_adapter.fetch(settings)
    assert s["equity"] == 31.0  # 25 cash + 10 shares * 0.6
    assert s["realized_pnl_total"] == 0.5 and s["realized_pnl_24h"] == 0.4  # journal legs
    p = s["positions"][0]
    assert p["whale"] == "Whale X" and p["pnl"] == 1.0 and p["sl"] == 0.4
    assert s["health"] == "green"
    assert digest(settings.poly_portfolio) == before


def test_polyfollow_journal_missing_falls_back(settings):
    settings.poly_journal += ".missing"
    assert polyfollow_adapter.fetch(settings)["realized_pnl_24h"] == 0.3


def test_polyfollow_paused_and_api_down(settings, monkeypatch):
    with open(settings.hermes_jobs, "w") as f:
        json.dump({"jobs": [{"id": "job1", "enabled": False, "state": "paused"}]}, f)
    s = polyfollow_adapter.fetch(settings)
    assert s["paused"] and s["health"] == "yellow"
    monkeypatch.setattr(polyfollow_adapter, "_api_ok", lambda s: False)
    assert polyfollow_adapter.fetch(settings)["health"] == "red"


def test_polyfollow_partial_json_raises(settings):
    with open(settings.poly_portfolio, "w") as f:
        f.write('{"cash_balance": 1')
    with pytest.raises(ValueError):
        polyfollow_adapter.fetch(settings)


def test_forex(settings):
    before = digest(settings.forex_db)
    s = forex_adapter.fetch(settings)
    assert s["equity"] == 1005.0 and s["health"] == "green"
    assert s["realized_pnl_total"] == 4.0 and s["realized_pnl_24h"] == 7.0
    p = s["positions"][0]
    assert p["side"] == "LONG" and p["roi_pct"] == 50.0 and p["tp"] == 2030.0
    assert digest(settings.forex_db) == before


def test_forex_stop_file_marks_yellow(settings):
    open(os.path.join(settings.forex_dir, "STOP"), "w").close()
    s = forex_adapter.fetch(settings)
    assert s["health"] == "yellow" and s["error"] == "STOP file present"


def test_system_forex_stop_idempotent(settings):
    ok, msg = system_adapter.forex_stop(settings)
    assert ok and os.path.exists(os.path.join(settings.forex_dir, "STOP"))
    ok, msg = system_adapter.forex_stop(settings)
    assert ok and "already" in msg


def test_system_restart_allowlist(settings, monkeypatch):
    calls = []
    monkeypatch.setattr(system_adapter, "_run", lambda cmd, timeout=30: (calls.append(cmd) or (True, "")))
    assert system_adapter.restart(settings, "forex-paper")[0]
    assert calls[-1] == ["sudo", "-n", "systemctl", "restart", "forex-paper"]
    system_adapter.restart(settings, "polyfollow-api")
    assert calls[-1] == ["docker", "restart", "polyfollow_api"]
    with pytest.raises(KeyError):
        system_adapter.restart(settings, "sshd")


def test_system_polymarket_uses_hermes(settings, monkeypatch):
    calls = []
    monkeypatch.setattr(system_adapter, "_run", lambda cmd, timeout=30: (calls.append(cmd) or (True, "ok")))
    system_adapter.polymarket(settings, "pause")
    assert calls[-1] == [settings.hermes_bin, "cron", "pause", "job1"]


def test_system_futures_command(settings, monkeypatch):
    seen = {}

    class R:
        status_code, text = 200, '{"queued":"pause"}'

    def post(url, params, headers, timeout):
        seen.update(url=url, headers=headers)
        return R()
    monkeypatch.setattr(system_adapter.httpx, "post", post)
    assert system_adapter.futures(settings, "pause")[0]
    assert seen["url"].endswith("/v1/commands/pause") and seen["headers"]["X-Api-Key"] == "k" * 20
    settings.assettrade_api_key = ""
    assert not system_adapter.futures(settings, "pause")[0]

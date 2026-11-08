import json
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from src import config
from src.adapters import polyfollow_adapter, system_adapter
from src.main import create_app

NOW = int(time.time())


def make_futures_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
    CREATE TABLE state (key TEXT PRIMARY KEY, value TEXT);
    CREATE TABLE fills (id INTEGER PRIMARY KEY, t INTEGER, mode TEXT, symbol TEXT, side TEXT,
      action TEXT, qty INTEGER, price REAL, fee REAL, pnl REAL, reason TEXT);""")
    snap = {"equity": 1050.0, "positions": [
        {"symbol": "BTC_USDT", "side": "long", "qty": 3, "entry": 100.0, "stop": 90.0, "opened_at": NOW - 3600}]}
    rows = {"snapshot": snap, "heartbeat": NOW, "paper_book": {"cash": 1000.0, "marks": {"BTC_USDT": 110.0}}}
    c.executemany("INSERT INTO state VALUES (?,?)", [(k, json.dumps(v)) for k, v in rows.items()])
    c.executemany("INSERT INTO fills (t, mode, action, fee, pnl) VALUES (?,?,?,?,?)", [
        (NOW - 10 * 86400, "paper", "close", 1.0, 20.0),
        (NOW - 100, "paper", "close", 0.5, 10.0),
        (NOW - 100, "paper", "open", 0.5, 0.0)])
    c.commit(); c.close()


def make_forex_db(path):
    c = sqlite3.connect(path)
    c.executescript("""
    CREATE TABLE account(id INTEGER PRIMARY KEY CHECK(id=1), balance REAL, day_start_equity REAL,
      day TEXT, daily_locked INTEGER, updated_at TEXT);
    CREATE TABLE positions(id TEXT PRIMARY KEY, symbol TEXT, side TEXT, lots REAL, entry_price REAL,
      sl REAL, tp REAL, open_time TEXT, initial_risk REAL, entry_reason TEXT, commission REAL, swap REAL,
      slippage_cost REAL, floating_pnl REAL);
    CREATE TABLE trades(id INTEGER PRIMARY KEY AUTOINCREMENT, position_id TEXT, run_id TEXT, mode TEXT,
      symbol TEXT, side TEXT, lots REAL, entry_price REAL, exit_price REAL, sl REAL, tp REAL, open_time TEXT,
      exit_time TEXT, commission REAL, swap REAL, slippage_cost REAL, gross_pnl REAL, net_pnl REAL,
      r_multiple REAL, entry_reason TEXT, exit_reason TEXT);
    INSERT INTO account VALUES (1, 1000.0, 1000.0, NULL, 0, '2026-11-08T16:18:00+00:00');
    INSERT INTO positions (id, symbol, side, lots, entry_price, sl, tp, open_time, initial_risk, floating_pnl)
      VALUES ('p1', 'XAUUSD', 'BUY', 0.1, 2000.0, 1990.0, 2030.0, '2026-11-08T10:00:00+00:00', 10.0, 5.0);
    INSERT INTO trades (net_pnl, exit_time) VALUES (-3.0, '2020-01-01T00:00:00+00:00');""")
    c.execute("INSERT INTO trades (net_pnl, exit_time) VALUES (7.0, ?)",
              (time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - 60)),))
    c.commit(); c.close()


def make_portfolio(path):
    recent = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - 600))
    path.write_text(json.dumps({
        "cash_balance": 25.0, "initial_capital": 30.0, "total_realized_pnl": 0.5,
        "open_positions": [{"market_title": "LoL: A vs B", "outcome": "A", "entry_price": 0.5, "current_price": 0.6,
                            "shares": 10.0, "cost_basis": 5.0, "unrealized_roi": 20.0, "entry_time": recent,
                            "copy_trader": "Whale X", "trader_win_rate": "90%", "tp_target": None, "sl_target": 0.4,
                            "price_stale": False}],
        "closed_positions": [{"realized_pnl": 0.3, "exit_time": recent},
                             {"realized_pnl": 0.2, "exit_time": "2020-01-01T00:00:00+00:00"}]}))


@pytest.fixture
def settings(tmp_path, monkeypatch):
    fut, fx = tmp_path / "bot_paper.db", tmp_path / "paper.db"
    make_futures_db(fut); make_forex_db(fx)
    pf = tmp_path / "paper_portfolio.json"; make_portfolio(pf)
    (tmp_path / "journal.json").write_text(json.dumps([
        {"realized_pnl": 0.3, "exit_time": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - 600))},
        {"realized_pnl": 0.1, "exit_time": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - 500))},
        {"realized_pnl": 0.2, "exit_time": "2020-01-01T00:00:00+00:00"}]))
    jobs = tmp_path / "jobs.json"
    jobs.write_text(json.dumps({"jobs": [{"id": "job1", "enabled": True, "state": "scheduled"}]}))
    forex_dir = tmp_path / "forex"; forex_dir.mkdir()
    s = config.Settings(dashboard_password="secret-pw", secret_key="x" * 32, assettrade_api_key="k" * 20,
                        hub_db=str(tmp_path / "hub.db"), snapshot_interval=0, futures_db=str(fut),
                        poly_portfolio=str(pf), poly_journal=str(tmp_path / "journal.json"), poly_cron_job="job1", hermes_jobs=str(jobs),
                        forex_db=str(fx), forex_dir=str(forex_dir))
    # no real network / systemd in tests
    monkeypatch.setattr(polyfollow_adapter, "_api_ok", lambda s: True)
    monkeypatch.setattr(system_adapter, "unit_state", lambda kind, name: "active")
    return s


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


@pytest.fixture
def authed(client):
    assert client.post("/api/login", json={"password": "secret-pw"}).status_code == 200
    return client

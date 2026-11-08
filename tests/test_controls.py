import os

from src.adapters import system_adapter


def test_forex_stop_endpoint(authed, settings):
    r = authed.post("/api/control/forex/stop")
    assert r.status_code == 200 and r.json()["ok"]
    assert os.path.exists(os.path.join(settings.forex_dir, "STOP"))
    log = authed.get("/api/actions").json()
    assert log[0]["action"] == "forex_stop" and log[0]["ok"]


def test_restart_not_allowed(authed):
    assert authed.post("/api/control/restart/sshd").status_code == 400


def test_restart_logs_failure(authed, monkeypatch):
    monkeypatch.setattr(system_adapter, "_run", lambda cmd, timeout=30: (False, "boom"))
    r = authed.post("/api/control/restart/forex-paper")
    assert r.status_code == 502
    log = authed.get("/api/actions").json()[0]
    assert log["target"] == "forex-paper" and not log["ok"] and log["message"] == "boom"


def test_pause_resume(authed, monkeypatch):
    calls = []
    monkeypatch.setattr(system_adapter, "_run", lambda cmd, timeout=30: (calls.append(cmd) or (True, "ok")))
    assert authed.post("/api/control/polymarket/pause").status_code == 200
    assert authed.post("/api/control/polymarket/resume").status_code == 200
    assert [c[2] for c in calls] == ["pause", "resume"]
    assert authed.post("/api/control/polymarket/delete").status_code == 400
    assert authed.post("/api/control/forex/pause").status_code == 400

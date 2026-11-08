import pytest

from src import config, store
from src.adapters import system_adapter
from src.main import snapshot_equity

PROTECTED = [("get", "/api/overview"), ("get", "/api/positions"), ("get", "/api/equity"),
             ("get", "/api/actions"), ("post", "/api/control/forex/stop"),
             ("post", "/api/control/restart/forex-paper"), ("post", "/api/control/polymarket/pause"),
             ("post", "/api/control/futures/pause")]


def test_health_and_index_public(client):
    assert client.get("/health").json() == {"ok": True}
    assert "Trading Hub" in client.get("/").text


@pytest.mark.parametrize("method,url", PROTECTED)
def test_requires_auth(client, method, url):
    assert getattr(client, method)(url).status_code == 401


def test_login_wrong_and_logout(client):
    assert client.post("/api/login", json={"password": "nope"}).status_code == 401
    assert client.post("/api/login", json={"password": "secret-pw"}).status_code == 200
    assert client.get("/api/overview").status_code == 200
    client.post("/api/logout")
    assert client.get("/api/overview").status_code == 401


def test_config_fails_closed(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    with pytest.raises(RuntimeError):
        config.load()


def test_overview(authed):
    d = authed.get("/api/overview").json()
    assert d["total"]["equity"] == 1050.0 + 31.0 + 1005.0
    assert d["total"]["open_positions"] == 3 and d["total"]["complete"]
    assert {b["bot"] for b in d["bots"]} == {"futures", "polymarket", "forex"}
    assert all("positions" not in b for b in d["bots"])


def test_overview_one_source_down(authed, settings):
    settings.forex_db = settings.forex_db + ".missing"
    d = authed.get("/api/overview").json()
    fx = next(b for b in d["bots"] if b["bot"] == "forex")
    assert fx["health"] == "red" and fx["equity"] is None
    assert d["total"]["equity"] == 1081.0 and not d["total"]["complete"]


def test_service_down_is_red(authed, monkeypatch):
    monkeypatch.setattr(system_adapter, "unit_state", lambda k, n: "inactive" if n == "forex-paper" else "active")
    fx = next(b for b in authed.get("/api/overview").json()["bots"] if b["bot"] == "forex")
    assert fx["health"] == "red" and "inactive" in fx["error"]


def test_positions_filter(authed):
    assert len(authed.get("/api/positions").json()) == 3
    poly = authed.get("/api/positions?platform=polymarket").json()
    assert len(poly) == 1 and poly[0]["whale"] == "Whale X"
    assert authed.get("/api/positions?platform=bogus").status_code == 400


def test_equity_snapshots(authed, settings):
    snapshot_equity(settings)
    pts = authed.get("/api/equity?bot=total&range=24h").json()
    assert len(pts) == 1 and pts[0]["equity"] == 2086.0
    assert len(authed.get("/api/equity?bot=forex&range=all").json()) == 1
    store.add_equity(settings.hub_db, {"forex": 900.0}, t=1)  # ancient point
    assert len(authed.get("/api/equity?bot=forex&range=7d").json()) == 1
    assert len(authed.get("/api/equity?bot=forex&range=all").json()) == 2
    assert authed.get("/api/equity?range=1y").status_code == 400


def test_snapshot_skips_partial_total(settings):
    settings.forex_db += ".missing"
    snapshot_equity(settings)
    assert store.equity(settings.hub_db, "total", "all") == []
    assert len(store.equity(settings.hub_db, "futures", "all")) == 1

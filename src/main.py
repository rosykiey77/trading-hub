"""Trading Hub: FastAPI app serving the dashboard and JSON API."""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from . import auth, config, store
from .adapters import forex_adapter, futures_adapter, polyfollow_adapter, system_adapter

log = logging.getLogger("trading-hub")
ADAPTERS = {"futures": futures_adapter, "polymarket": polyfollow_adapter, "forex": forex_adapter}
NAMES = {"futures": "AssetTrade Futures", "polymarket": "PolyFollow Polymarket", "forex": "Forex & Gold"}


def collect(s) -> list[dict]:
    """One snapshot per bot; a failing source yields a red entry instead of breaking the others."""
    states = system_adapter.service_states(s)
    out = []
    for bot, ad in ADAPTERS.items():
        try:
            snap = ad.fetch(s)
        except Exception as e:  # noqa: BLE001 - any source failure must stay isolated
            log.warning("%s adapter failed: %s", bot, e)
            snap = {"bot": bot, "name": NAMES[bot], "health": "red", "equity": None, "cash": None,
                    "realized_pnl_total": None, "realized_pnl_24h": None, "open_positions": 0,
                    "paused": False, "updated_at": None, "error": f"source unavailable: {e}", "positions": []}
        state = states.get(bot)
        snap["service"] = state
        if state not in ("active", "running"):
            snap["health"] = "red"
            snap["error"] = snap["error"] or f"service {state}"
        out.append(snap)
    return out


def totals(bots: list[dict]) -> dict:
    s = lambda k: round(sum(b[k] or 0 for b in bots), 2)  # noqa: E731
    return {"equity": s("equity"), "realized_pnl_total": s("realized_pnl_total"),
            "realized_pnl_24h": s("realized_pnl_24h"), "open_positions": sum(b["open_positions"] for b in bots),
            "complete": all(b["equity"] is not None for b in bots)}


def snapshot_equity(s) -> None:
    bots = collect(s)
    vals = {b["bot"]: b["equity"] for b in bots}
    if all(v is not None for v in vals.values()):  # partial totals would draw fake drops
        vals["total"] = totals(bots)["equity"]
    store.add_equity(s.hub_db, vals)


class Login(BaseModel):
    password: str


def create_app(s=None) -> FastAPI:
    s = s or config.load()
    store.connect(s.hub_db).close()

    @asynccontextmanager
    async def lifespan(app):
        task = None
        if s.snapshot_interval > 0:
            async def loop():
                while True:
                    try:
                        await asyncio.to_thread(snapshot_equity, s)
                    except Exception as e:  # noqa: BLE001
                        log.warning("snapshot failed: %s", e)
                    await asyncio.sleep(s.snapshot_interval)
            task = asyncio.create_task(loop())
        yield
        if task:
            task.cancel()

    app = FastAPI(title="Trading Hub", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(SessionMiddleware, secret_key=s.secret_key, same_site="strict",
                       max_age=7 * 86400, session_cookie="hub_session")
    app.mount("/static", StaticFiles(directory=config.ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=config.ROOT / "templates")
    authed = [Depends(auth.require_auth)]

    def act(action: str, target: str, fn):
        try:
            ok, msg = fn()
        except Exception as e:  # noqa: BLE001
            ok, msg = False, str(e)
        store.log_action(s.hub_db, action, target, ok, msg)
        if not ok:
            raise HTTPException(502, msg)
        return {"ok": True, "message": msg}

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse(request, "index.html")

    @app.post("/api/login")
    async def login(body: Login, request: Request):
        if not await auth.login(request, body.password, s.dashboard_password):
            raise HTTPException(401, "invalid password")
        return {"ok": True}

    @app.post("/api/logout")
    def logout(request: Request):
        request.session.clear()
        return {"ok": True}

    @app.get("/api/overview", dependencies=authed)
    def overview():
        bots = collect(s)
        for b in bots:
            b.pop("positions")
        return {"total": totals(bots), "bots": bots, "time": datetime.now(timezone.utc).isoformat()}

    @app.get("/api/positions", dependencies=authed)
    def positions(platform: str | None = None):
        if platform and platform not in ADAPTERS:
            raise HTTPException(400, "unknown platform")
        return [p for b in collect(s) if not platform or b["bot"] == platform for p in b["positions"]]

    @app.get("/api/equity", dependencies=authed)
    def equity(bot: str = "total", range: str = "7d"):  # noqa: A002 - query param name from contract
        if bot not in (*ADAPTERS, "total") or range not in store.RANGES:
            raise HTTPException(400, "bad bot or range")
        return store.equity(s.hub_db, bot, range)

    @app.get("/api/actions", dependencies=authed)
    def actions():
        return store.actions(s.hub_db)

    @app.post("/api/control/forex/stop", dependencies=authed)
    def forex_stop():
        return act("forex_stop", "forex", lambda: system_adapter.forex_stop(s))

    @app.post("/api/control/restart/{target}", dependencies=authed)
    def restart(target: str):
        if target not in s.restart_targets:
            raise HTTPException(400, "target not allowed")
        return act("restart", target, lambda: system_adapter.restart(s, target))

    @app.post("/api/control/{bot}/{cmd}", dependencies=authed)
    def pause_resume(bot: str, cmd: str):
        if bot not in ("polymarket", "futures") or cmd not in ("pause", "resume"):
            raise HTTPException(400, "unknown control")
        fn = system_adapter.polymarket if bot == "polymarket" else system_adapter.futures
        return act(cmd, bot, lambda: fn(s, cmd))

    return app

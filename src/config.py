"""Settings from environment / .env. Fails closed without DASHBOARD_PASSWORD."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    dashboard_password: str
    secret_key: str
    assettrade_api_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8200
    hub_db: str = str(ROOT / "data" / "hub.db")
    snapshot_interval: int = 300  # seconds; 0 disables the background loop
    futures_db: str = "/opt/assettrade/data/bot_paper.db"
    futures_api: str = "http://127.0.0.1:8100"
    poly_portfolio: str = "/home/ubuntu/polyfollow/paper_portfolio.json"
    poly_journal: str = "/home/ubuntu/polyfollow/trading_journal.json"  # every leg, incl. partial TPs
    poly_api: str = "http://127.0.0.1:8899"
    poly_cron_job: str = "63a3f44ce7d3"
    hermes_jobs: str = "/home/ubuntu/.hermes/cron/jobs.json"
    hermes_bin: str = "/home/ubuntu/.local/bin/hermes"
    forex_db: str = "/home/ubuntu/forex-trend-bot/data/paper.db"
    forex_dir: str = "/home/ubuntu/forex-trend-bot"
    # bot id -> service it depends on, used for the health pill
    services: dict = field(default_factory=lambda: {
        "futures": ("systemd", "assettrade-bot@paper"),
        "polymarket": ("docker", "polyfollow_api"),
        "forex": ("systemd", "forex-paper"),
    })
    # restart allow-list: target -> (kind, unit/container)
    restart_targets: dict = field(default_factory=lambda: {
        "assettrade-bot": ("systemd", "assettrade-bot@paper"),
        "assettrade-api": ("systemd", "assettrade-bot-api"),
        "forex-paper": ("systemd", "forex-paper"),
        "polyfollow-api": ("docker", "polyfollow_api"),
    })


def load() -> Settings:
    load_dotenv(ROOT / ".env")
    pw = os.environ.get("DASHBOARD_PASSWORD", "")
    secret = os.environ.get("SECRET_KEY", "")
    if not pw or len(secret) < 16:
        raise RuntimeError("DASHBOARD_PASSWORD and SECRET_KEY (>=16 chars) must be set in .env")
    s = Settings(dashboard_password=pw, secret_key=secret)
    env = {k.upper(): k for k in Settings.__dataclass_fields__}
    for ENV, attr in env.items():
        if ENV in os.environ and attr not in ("dashboard_password", "secret_key"):
            cur = getattr(s, attr)
            if isinstance(cur, (str, int)):
                setattr(s, attr, type(cur)(os.environ[ENV]))
    return s

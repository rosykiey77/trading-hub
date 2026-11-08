# trading-hub
Unified Web Dashboard for Multi-Market Trading Automation:
- **Crypto Futures** (AssetTrade 4H Trend Bot / MEXC)
- **Polymarket Copy-Trading** (PolyFollow Whale Paper/Live)
- **Forex & Gold Bot** (TradingAgents Daily Bias + H1 Pullback / MT5)

Features:
- Single-page real-time responsive UI (Tailwind CSS + Chart.js / Lightweight Charts)
- Consolidated Portfolio Overview (Total Equity, PnL, Drawdown)
- Open Positions & Active Whales Monitor
- Emergency Controls (Kill Switches / Stop Individual Bots)
- Lightweight FastAPI Backend with Read-Only DB & API Adapters

## Run

```bash
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env        # set DASHBOARD_PASSWORD, SECRET_KEY, ASSETTRADE_API_KEY
.venv/bin/python -m pytest -q
sudo cp deploy/trading-hub.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now trading-hub
```

Dashboard: `http://<host>:8200`. Docs: `docs/spec.md`, `docs/plan.md`, `docs/tasks.md`, `docs/contracts/api.md`.
Read-only toward the bots; the only writes outside this repo are the Forex `STOP` file and the allow-listed restart/pause commands.

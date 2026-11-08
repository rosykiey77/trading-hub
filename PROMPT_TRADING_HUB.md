# PROMPT_TRADING_HUB.md — Unified Trading Web Dashboard

## Overview & Goals
Build a lightweight, responsive, real-time single-page Web Dashboard and API hub (`trading-hub`) that consolidates all 3 trading bots running on this Ubuntu VPS:
1. **AssetTrade Crypto Futures**: MEXC 4H Trend-Following Bot (`/opt/assettrade`, local API `http://127.0.0.1:8100`, read-only SQLite `/opt/assettrade/data/bot_paper.db`).
2. **PolyFollow Polymarket Copy-Trading**: Whale tracker & Paper/Live Engine (`/home/ubuntu/polyfollow`, API `http://127.0.0.1:8899`, portfolio `/home/ubuntu/polyfollow/paper_portfolio.json`, SQLite `/home/ubuntu/polyfollow/polyfollow.db`).
3. **Forex & Gold Bot**: TradingAgents Daily Bias + H1 Pullback (`/home/ubuntu/forex-trend-bot`, SQLite `/home/ubuntu/forex-trend-bot/data/paper.db`, service `forex-paper.service`).

Target Audience: The user accesses this dashboard via browser on mobile (phone) or desktop/laptop. Must be ultra-fast, mobile-friendly (Tailwind dark mode), reliable, and require zero heavy build steps (single self-contained FastAPI server serving clean HTML/JS/CSS or Alpine.js/Tailwind CDN with Chart.js).

---

## Key Requirements & Features

### 1. Unified Portfolio KPI Summary (Top Cards)
- **Total Combined Equity** (USD/USDT): Sum of Futures Equity + Polymarket Balance + Forex Equity.
- **24h / Total Realized PnL**: Consolidated profit/loss.
- **Active Open Positions Count**: Total across all 3 markets.
- **Bot Health Status**: Green/Yellow/Red status pill for each of the 3 bot services.

### 2. Multi-Market Open Positions & Live Orders
- Tabbed or unified table showing:
  - Market / Asset (`BTC_USDT`, `ETH_USDT`, `LoL Esports`, `EURUSD`, `XAUUSD`, etc.)
  - Platform tag (`Futures`, `Polymarket`, `Forex`)
  - Direction (`LONG / UP / BUY` vs `SHORT / DOWN / SELL`)
  - Entry Price, Current Price, Unrealized PnL / ROI %
  - Stop Loss & Take Profit targets
  - Duration open & Copy Whale info (if Polymarket)

### 3. Consolidated Equity & PnL Curve
- Interactive Chart (Chart.js or TradingView Lightweight Charts via CDN).
- Switchable view: All combined vs individual bot curve.

### 4. Emergency Action Controls (Protected Panic Buttons)
- Direct actions via backend API with double-click / modal confirmation:
  - **Emergency Stop Forex Bot** (creates `STOP` file in `/home/ubuntu/forex-trend-bot/STOP` which triggers native emergency flatten & shutdown).
  - **Restart / Reload Services** (safe health restart via systemctl / docker without code changes).
  - **Pause Copy-Trading** on PolyFollow.
- Basic security: Dashboard protected by a clean session token or password set in `.env` (`DASHBOARD_PASSWORD`), so public access via VPS IP requires auth.

### 5. Architectural Principles & Constraints
- **Read-Only / Isolated**: Must never modify `/opt/assettrade` code or data directly. Read SQLite databases in read-only URI mode (`file:...db?mode=ro`).
- **Zero Heavy Frontend Scaffolding**: Use FastAPI + Jinja2 templates + Tailwind CSS CDN + Chart.js CDN + Vanilla JS/Alpine.js. Fast to launch, 0 Node.js build overhead, instant startup.
- **Systemd Daemon**: Serves on `0.0.0.0:8200` (or configurable in `config.yaml` / `.env`) as `trading-hub.service`.
- **Unit Tests**: Test data adapters for each bot, authentication, emergency actions, and API endpoints using `pytest`.

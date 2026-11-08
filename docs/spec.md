# Feature Specification: Unified Trading Dashboard (Trading Hub)

**Feature Branch**: `main` (feature directory: `docs/`)
**Created**: 2026-11-08
**Status**: Draft
**Input**: User description: "Unified Trading Dashboard (FastAPI backend + responsive Tailwind/Alpine/Chart.js SPA) integrating AssetTrade Crypto Futures (API :8100, read-only DB /opt/assettrade/data/bot_paper.db), PolyFollow Polymarket (API :8899, /home/ubuntu/polyfollow/paper_portfolio.json), Forex Trend Bot (SQLite /home/ubuntu/forex-trend-bot/data/paper.db). Features: Total KPI equity, live positions, PnL chart, bot status pills, password auth, panic button (STOP file & safe restart). Read-only: never modify other bots' code or DBs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the whole portfolio at a glance (Priority: P1)

The operator opens the dashboard on a phone or laptop and immediately sees combined equity across the three bots (Crypto Futures, Polymarket, Forex), realized PnL (24h and all-time), number of open positions, and a green/yellow/red health pill per bot.

**Why this priority**: This is the core reason the dashboard exists — one place instead of three tools.

**Independent Test**: Log in, load the page, compare totals against each bot's own source of truth.

**Acceptance Scenarios**:

1. **Given** all three bots are reachable, **When** the operator opens the dashboard, **Then** Total Equity equals the sum of the three per-bot equities, shown per bot as well.
2. **Given** one bot's data source is unavailable, **When** the dashboard loads, **Then** the other two bots still display, the unavailable bot's pill is red, and its value is marked as missing rather than shown as zero.
3. **Given** the page is open, **When** 15 seconds pass, **Then** the figures refresh without a manual reload.

### User Story 2 - Monitor live positions across markets (Priority: P1)

The operator sees every open position in one list with platform tag, asset, direction, entry price, current price, unrealized PnL/ROI, stop-loss/take-profit, time open, and (for Polymarket) the copied whale. Filter tabs: All / Crypto Futures / Polymarket / Forex. Cards on mobile, table on desktop.

**Why this priority**: Positions are where money is at risk.

**Independent Test**: With known open positions in a bot, the list shows each one with correct fields; the filter shows only that platform.

**Acceptance Scenarios**:

1. **Given** PolyFollow has 3 open positions, **When** the operator picks the Polymarket tab, **Then** exactly those 3 are listed with whale name and win rate.
2. **Given** a bot has no open positions, **When** the list loads, **Then** an empty-state message is shown for that filter.

### User Story 3 - Equity / PnL curve (Priority: P2)

The operator views a line chart of equity over time, switchable between combined and individual bots, with ranges 24H / 7D / 30D / All.

**Why this priority**: Trend context; useful but secondary to current state.

**Independent Test**: After several refresh cycles the chart shows recorded points; switching bot or range changes the data shown.

**Acceptance Scenarios**:

1. **Given** equity history exists, **When** the operator selects "Forex" and "7D", **Then** only Forex points from the last 7 days are drawn.

### User Story 4 - Emergency controls (Priority: P1)

The operator can, after an explicit confirmation step: (a) emergency-stop the Forex bot via its native STOP-file mechanism, (b) safely restart a bot service, (c) pause/resume PolyFollow copy-trading, (d) pause/resume the AssetTrade futures runner through its own command channel.

**Why this priority**: Risk control is safety-critical when away from a terminal.

**Independent Test**: Trigger each action against a test environment and verify the expected side effect (STOP file present, service restarted, job paused) and an audit record.

**Acceptance Scenarios**:

1. **Given** the operator clicks "Emergency Stop Forex", **When** they confirm in the modal, **Then** the STOP file is created in the Forex bot directory and the action is logged.
2. **Given** the operator clicks a control but cancels the modal, **Then** nothing happens.
3. **Given** an unauthenticated request to any control, **Then** it is rejected and no action is taken.
4. **Given** a restart request for a service not on the allow-list, **Then** it is rejected.

### User Story 5 - Password protection (Priority: P1)

The dashboard is reachable on the VPS public IP, so every page and data endpoint requires login with a password configured by the operator. The operator can log out.

**Why this priority**: Without it, anyone could see balances or trigger panic actions.

**Independent Test**: Request any data endpoint without a session → rejected; log in with correct password → allowed; wrong password → rejected.

**Acceptance Scenarios**:

1. **Given** no session, **When** the dashboard URL is opened, **Then** the login screen is shown and no portfolio data is returned.
2. **Given** a wrong password, **When** submitted, **Then** login fails with a generic message.

### Edge Cases

- A bot's data file is mid-write (partial JSON) → keep last good value for that bot, mark as stale.
- A bot's database is locked by its writer → read retries/fails gracefully, never blocks or alters the writer.
- A bot service is running but its heartbeat is old → yellow pill.
- No password configured → the dashboard refuses to start (fails closed).
- Polymarket position with a stale price → shown with a "stale" marker.
- Forex STOP file already exists → action reports "already stopped", is idempotent.
- Bot equity history is empty (new bots) → chart builds from the hub's own periodic snapshots.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST show Total Combined Equity = Futures equity + Polymarket equity (cash + open position value) + Forex equity, plus each component.
- **FR-002**: System MUST show realized PnL for the last 24h and all-time, per bot and combined.
- **FR-003**: System MUST show the total count of open positions across all bots.
- **FR-004**: System MUST show a health pill per bot: green (running and fresh), yellow (running but data stale / paused), red (down or unreachable).
- **FR-005**: System MUST list open positions with platform, asset, direction, entry, current price, unrealized PnL/ROI, SL/TP, time open, and copy-whale info where applicable, filterable by platform.
- **FR-006**: System MUST provide an equity chart (combined or per-bot; 24H/7D/30D/All), recording its own periodic equity snapshots in its own storage.
- **FR-007**: System MUST require password authentication (password from operator-controlled configuration) for all pages, data and control endpoints except login and a liveness check.
- **FR-008**: System MUST offer an Emergency Stop for the Forex bot that creates the bot's STOP file and nothing else.
- **FR-009**: System MUST offer safe restart limited to an explicit allow-list of bot services/containers.
- **FR-010**: System MUST offer pause/resume of PolyFollow copy-trading and AssetTrade futures trading using only each bot's own existing control mechanism.
- **FR-011**: Every control action MUST require a confirmation step in the UI and MUST be logged (time, action, result).
- **FR-012**: System MUST NEVER modify other bots' code, configuration, or databases; database access MUST be read-only.
- **FR-013**: System MUST degrade per bot: a failure in one bot source never hides the others.
- **FR-014**: UI MUST be dark-themed, mobile-first responsive, and auto-refresh every 15 s; it shows server clock in WIB and UTC.
- **FR-015**: System MUST run as a persistent service that restarts on failure and listens on port 8200 (configurable).

### Key Entities

- **BotSnapshot**: bot id, name, health (green/yellow/red), equity, cash, realized PnL (24h, total), open position count, last update time, error message.
- **Position**: platform, asset, direction, size, entry, current, unrealized PnL, ROI %, SL, TP, opened at, whale (Polymarket), stale flag.
- **EquityPoint**: time, bot id (or "total"), equity — stored by the hub.
- **ControlAction log entry**: time, action, target, success, message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operator sees combined equity and all bot statuses within 3 seconds of opening the dashboard on a mobile connection.
- **SC-002**: Displayed totals match each bot's own source to the cent at the time of refresh.
- **SC-003**: 100% of data and control requests without a valid session are rejected.
- **SC-004**: Emergency Stop for Forex takes effect (bot begins its own shutdown) within 60 seconds of confirmation.
- **SC-005**: If any single bot is down, the remaining bots' data is still visible 100% of the time.
- **SC-006**: Zero writes to any other bot's database or code directory, verified by tests.
- **SC-007**: Dashboard is usable without horizontal scrolling on a 375px-wide screen.

## Assumptions

- Single operator; one shared password (no multi-user roles).
- Polymarket equity = cash balance + sum of open position value (shares × current price).
- AssetTrade richer status needs its API key; the hub reads it from its own config. If absent, the hub falls back to the bot's read-only database snapshot.
- PolyFollow paper engine runs as a scheduled job; "pause copy-trading" means pausing that scheduled job via its scheduler's own command.
- Hub's own data (equity snapshots, action log) lives in the hub's own directory.
- Restart allow-list: `assettrade-bot@paper`, `assettrade-bot-api`, `forex-paper` services and the `polyfollow_api` container.
- Removing the Forex STOP file (resuming) is a manual operator task, out of scope.

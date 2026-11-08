# Research: Trading Hub

Findings from inspecting the live bots on 2026-11-08.

## AssetTrade (Crypto Futures)
- **Decision** (revised during implementation): read `/opt/assettrade/data/bot_paper.db` read-only (`state`: `snapshot`, `heartbeat`, `paper_book.marks`, `paused`; `fills` for realized PnL). This is exactly what the bot's own `/v1/status` reads, so it needs no API key and has no extra failure point. The API key (`ASSETTRADE_API_KEY` in hub `.env`) is used only for pause/resume commands.
- Futures position PnL in $ is not shown: snapshot has contract `qty`, not contract size. ROI % comes from mark vs entry.
- Controls: `POST /v1/commands/{pause|resume|flatten}` — the bot's own queue; runner applies within ~20 s.
- Services: `assettrade-bot@paper.service`, `assettrade-bot-api.service`.

## PolyFollow (Polymarket)
- **Decision**: Read `/home/ubuntu/polyfollow/paper_portfolio.json` (`cash_balance`, `initial_capital`, `total_realized_pnl`, `open_positions[]`, `closed_positions[]` with `exit_time`/`realized_pnl`). Health from `GET :8899/health` (`status`, `poller_running`).
- Equity = cash + Σ shares × current_price.
- 24h realized PnL comes from `trading_journal.json` (every leg, incl. partial TPs); `closed_positions` holds final legs only, so it is used only as a fallback.
- **Pause**: paper engine is Hermes cron job `polyfollow_paper_engine` (id `63a3f44ce7d3`, every 1 m). Pause/resume via `hermes cron pause|resume <id>` — Hermes' own CLI, no file edits.
- Restart target: docker container `polyfollow_api`.
- Alternatives rejected: editing `~/.hermes/cron/jobs.json` directly (races the scheduler, modifies another system's state).

## Forex Trend Bot
- **Decision**: Read `/home/ubuntu/forex-trend-bot/data/paper.db` (`mode=ro`): `account.balance`, `positions` (+ `floating_pnl`), `trades.net_pnl/exit_time`, `equity` table, `events`.
- Equity = balance + Σ floating_pnl.
- **Emergency stop**: bot's `RiskManager` kills itself when `STOP` exists in its working dir `/home/ubuntu/forex-trend-bot` (poll 10 s). Hub creates that empty file only.
- Service: `forex-paper.service`.

## System health / restart
- `systemctl is-active <unit>`; `docker inspect -f {{.State.Status}}` for containers.
- Restart: `sudo -n systemctl restart <unit>` / `docker restart <name>`, only for an allow-list; args passed as list (no shell).

## Equity history
- Bots have little/no equity history (AssetTrade none, Forex `equity` empty). **Decision**: hub background task writes one snapshot per bot + total every 5 min to `data/hub.db`; chart reads that. Prune not needed at this scale (≈100k rows/yr).

## Auth
- **Decision**: single password from `DASHBOARD_PASSWORD`; `hmac.compare_digest`; signed cookie via Starlette `SessionMiddleware` (`SECRET_KEY`), `httponly`, `samesite=strict`. App refuses to start without a password.

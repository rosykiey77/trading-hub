# Implementation Plan: Unified Trading Dashboard (Trading Hub)

**Branch**: `main` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `docs/spec.md`

## Summary

One FastAPI process serves a Jinja2 single page (Tailwind/Alpine/Chart.js/Lucide via CDN) and a small JSON API. Three read-only adapters normalize each bot into a common `BotSnapshot` + `Position` shape; a system adapter reports service health and performs the allow-listed control actions using each bot's own native mechanism. The hub records its own equity snapshots in `data/hub.db` (the bots keep little or no equity history). Runs as `trading-hub.service` on `0.0.0.0:8200`.

## Technical Context

**Language/Version**: Python 3.12 (system `/usr/bin/python3`, project venv `.venv`)
**Primary Dependencies**: fastapi, uvicorn, jinja2, httpx, python-dotenv, itsdangerous (signed session cookie); pytest for tests
**Storage**: Bots read-only (`sqlite3` URI `mode=ro`, JSON file reads); hub-owned SQLite `data/hub.db` (equity snapshots, action log)
**Testing**: pytest + FastAPI TestClient; adapters tested against temp fixture DBs/JSON and mocked HTTP
**Target Platform**: Ubuntu VPS, systemd
**Project Type**: web service + server-rendered SPA
**Performance Goals**: `/api/overview` < 1 s (local reads only; HTTP timeouts 3 s)
**Constraints**: never write to other bots' files/DBs; fail closed if `DASHBOARD_PASSWORD` unset; no Node build
**Scale/Scope**: 1 operator, 3 bots, refresh every 15 s

## Constitution Check

`.specify/memory/constitution.md` is still the unfilled template — no ratified gates. Applied the project's own constraints from PROMPT_TRADING_HUB.md as gates instead:

| Gate | Status |
|------|--------|
| Read-only access to other bots (`mode=ro`, no writes) | PASS — adapters only read; tests assert DB unchanged |
| No heavy frontend scaffolding | PASS — CDN only |
| Auth on all data/control endpoints | PASS — session dependency on every `/api/*` except `/api/login`, `/health` |
| Unit tests for adapters, auth, controls, API | PASS — planned in `tests/` |

Post-design re-check: PASS (no new violations).

## Project Structure

### Documentation (this feature)

```text
docs/
├── spec.md
├── plan.md          # this file
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/api.md
└── tasks.md         # /speckit-tasks
```

### Source Code (repository root)

```text
src/
├── main.py              # FastAPI app, routes, background snapshot loop
├── config.py            # Settings from .env
├── auth.py              # login/logout, session dependency
├── store.py             # hub.db: equity snapshots + action log
└── adapters/
    ├── futures_adapter.py     # AssetTrade: bot_paper.db (ro); API :8100 only for commands
    ├── polyfollow_adapter.py  # paper_portfolio.json + API :8899 /health
    ├── forex_adapter.py       # forex paper.db (ro)
    └── system_adapter.py      # systemctl/docker status; STOP file; restart; pause/resume
templates/index.html
static/app.js
tests/
deploy/trading-hub.service
requirements.txt
.env.example
```

**Structure Decision**: Single project; routes live in `src/main.py` (≈ a dozen endpoints — splitting into routers adds nothing).

## Complexity Tracking

None.

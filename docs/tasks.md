# Tasks: Unified Trading Dashboard (Trading Hub)

**Input**: Design documents from `docs/` (spec.md, plan.md, research.md, data-model.md, contracts/api.md, quickstart.md)
**Tests**: Requested by user (unit tests for adapters + API, pytest must pass 100%).

## Phase 1: Setup

- [x] T001 Create layout `src/`, `src/adapters/`, `templates/`, `static/`, `tests/`, `deploy/`, `data/` per plan.md
- [x] T002 Create `requirements.txt` (fastapi, uvicorn, jinja2, httpx, python-dotenv, itsdangerous, pytest) and `.venv`
- [x] T003 [P] Create `.env.example` (DASHBOARD_PASSWORD, SECRET_KEY, ASSETTRADE_API_KEY, HOST, PORT, paths) and real `.env` (gitignored)

## Phase 2: Foundational

- [x] T004 Implement settings loader in `src/config.py` — refuse start when `DASHBOARD_PASSWORD` empty
- [x] T005 Implement hub storage in `src/store.py`: tables `equity(t INTEGER, bot TEXT, equity REAL, PK(t,bot))`, `actions(t, action, target, ok, message)`
- [x] T006 Implement auth in `src/auth.py`: constant-time password check, session flag, `require_auth` dependency (401)
- [x] T007 Create app skeleton `src/main.py`: SessionMiddleware, `/health`, `/api/login`, `/api/logout`, static + template mount
- [x] T008 [P] Shared test fixtures in `tests/conftest.py`: temp fixture DBs/JSON for each bot, settings override, logged-in client

## Phase 3: User Story 5 — Password protection (P1)

- [x] T009 [P] [US5] Tests in `tests/test_auth.py`: 401 without session, wrong password 401, correct → 200, logout clears

## Phase 4: User Story 1 — Portfolio at a glance (P1) 🎯 MVP

- [x] T010 [P] [US1] `src/adapters/futures_adapter.py`: API `/v1/status` + `/v1/report` with X-Api-Key, fallback `state`/`fills` in bot_paper.db opened `mode=ro`; health "red = source unreachable/service down; yellow = paused or stale (>15 min heartbeat)"
- [x] T011 [P] [US1] `src/adapters/polyfollow_adapter.py`: read paper_portfolio.json, equity = cash + Σ shares×current_price, 24h PnL from `closed_positions.exit_time`, health from `:8899/health`
- [x] T012 [P] [US1] `src/adapters/forex_adapter.py`: ro read of `account`, `positions`, `trades`, `events`; equity = balance + Σ floating_pnl
- [x] T013 [P] [US1] `src/adapters/system_adapter.py`: `service_states()` via `systemctl is-active` / `docker inspect`
- [x] T014 [US1] `GET /api/overview` in `src/main.py`, per-bot try/except so one failure never hides others (`equity` null, not 0)
- [x] T015 [P] [US1] Tests `tests/test_adapters.py` (each adapter, fixture data, missing source → red, DB unchanged after read)

## Phase 5: User Story 2 — Live positions (P1)

- [x] T016 [US2] `GET /api/positions?platform=` in `src/main.py` using adapters' `positions()`
- [x] T017 [P] [US2] Tests in `tests/test_api.py` for positions + filter

## Phase 6: User Story 4 — Emergency controls (P1)

- [x] T018 [US4] In `src/adapters/system_adapter.py`: `forex_stop()` (create STOP only, idempotent), `restart(target)` allow-list only, `polymarket_pause/resume` via `hermes cron pause|resume <id>`, futures pause/resume via `POST /v1/commands/{cmd}`
- [x] T019 [US4] `POST /api/control/...` endpoints + action log in `src/main.py`, `GET /api/actions`
- [x] T020 [P] [US4] Tests in `tests/test_controls.py` (subprocess mocked; STOP file in tmp dir; non-allowlisted → 400; unauth → 401)

## Phase 7: User Story 3 — Equity chart (P2)

- [x] T021 [US3] Background snapshot loop (every 5 min) in `src/main.py` writing to `store.equity`
- [x] T022 [US3] `GET /api/equity?bot=&range=` in `src/main.py`
- [x] T023 [P] [US3] Tests for store + equity endpoint in `tests/test_api.py`

## Phase 8: Frontend (US1–US5 UI)

- [x] T024 `templates/index.html`: login view, header (live dot, WIB/UTC clock, net worth, logout), 4 KPI cards, chart with bot/range toggles, positions tabs (cards mobile / table desktop), controls panel with confirm modal, action log — per docs/design.md
- [x] T025 `static/app.js`: Alpine component, 15 s polling, 401 → login, Chart.js line with gradient

## Phase 9: Polish & Deploy

- [x] T026 `deploy/trading-hub.service` (User=ubuntu, port 8200, Restart=always); install, enable, verify running
- [x] T027 Run `pytest` → 100% pass; smoke test per `docs/quickstart.md`; update README

## Dependencies

Setup → Foundational → US5 → US1 → (US2, US4, US3 parallel) → Frontend → Deploy.
Parallel: T010–T013 (different adapter files); test files T015/T017/T020/T023.

## Implementation Strategy

MVP = Phases 1–4 (auth + overview). Then positions, controls, chart, UI, deploy.

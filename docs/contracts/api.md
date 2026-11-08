# HTTP API (all JSON; all `/api/*` except login require session cookie → 401 otherwise)

| Method | Path | Body / Query | Response |
|---|---|---|---|
| GET | `/health` | – | `{"ok": true}` (no auth) |
| GET | `/` | – | dashboard HTML (login form rendered client-side when 401) |
| POST | `/api/login` | `{"password"}` | 200 `{"ok":true}` + cookie, 401 on wrong |
| POST | `/api/logout` | – | `{"ok":true}` |
| GET | `/api/overview` | – | `{"total":{equity,realized_pnl_total,realized_pnl_24h,open_positions}, "bots":[BotSnapshot], "services":{unit: state}, "time": iso}` |
| GET | `/api/positions` | `?platform=futures|polymarket|forex` | `[Position]` |
| GET | `/api/equity` | `?bot=total|futures|polymarket|forex&range=24h|7d|30d|all` | `[{"t":unix,"equity":float}]` |
| GET | `/api/actions` | – | last 50 ActionLog entries |
| POST | `/api/control/forex/stop` | – | `{"ok","message"}` creates STOP file |
| POST | `/api/control/restart/{target}` | target ∈ allow-list | `{"ok","message"}`; 400 if not allowed |
| POST | `/api/control/polymarket/{pause|resume}` | – | `{"ok","message"}` |
| POST | `/api/control/futures/{pause|resume}` | – | `{"ok","message"}` |

Restart allow-list targets: `assettrade-bot` (`assettrade-bot@paper`), `assettrade-api` (`assettrade-bot-api`), `forex-paper`, `polyfollow-api` (docker `polyfollow_api`).

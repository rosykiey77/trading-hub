# Data Model

## BotSnapshot (computed per request)
| field | type | note |
|---|---|---|
| bot | `futures` \| `polymarket` \| `forex` | |
| name | str | display name |
| health | `green` \| `yellow` \| `red` | red = source unreachable/service down; yellow = paused or stale (>15 min heartbeat) |
| equity | float \| null | null when unavailable (never 0 by default) |
| cash | float \| null | |
| realized_pnl_total | float | |
| realized_pnl_24h | float | |
| open_positions | int | |
| paused | bool | |
| updated_at | ISO str \| null | |
| error | str \| null | |

## Position
platform, symbol, side (`LONG`/`SHORT`/outcome), size, entry, current, pnl, roi_pct, sl, tp, opened_at, whale, whale_win_rate, stale.

## EquityPoint (hub.db `equity`)
`t INTEGER` (unix), `bot TEXT` (`futures|polymarket|forex|total`), `equity REAL`. PK (t, bot).

## ActionLog (hub.db `actions`)
`t INTEGER`, `action TEXT`, `target TEXT`, `ok INTEGER`, `message TEXT`.

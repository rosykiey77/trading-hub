# Design System & UI Specifications — Trading Hub Web Dashboard

## Theme & Aesthetic
- **Dark Mode First**: One UI / FinTech modern dark theme (`bg-slate-950`, cards `bg-slate-900/90`, border `border-slate-800`).
- **Accent Colors**:
  - Emerald / Green: Profit, LONG, BUY, Healthy (`text-emerald-400`, `bg-emerald-500/10`)
  - Rose / Red: Loss, SHORT, SELL, Warning (`text-rose-400`, `bg-rose-500/10`)
  - Cyan / Blue: Crypto Futures (`text-cyan-400`)
  - Violet / Purple: Polymarket (`text-purple-400`)
  - Amber / Gold: Forex / XAUUSD (`text-amber-400`)

## Layout (Mobile Responsive)
1. **Header / Navbar**:
   - Title: `Trading Hub` with live blinking status dot (connected).
   - Server Clock (WIB & UTC).
   - Total Net Worth counter with animated pulse on change.
   - Lock/Logout button.

2. **KPI Stat Cards Grid** (4 columns on desktop, 2x2 on mobile):
   - Card 1: Total Equity ($) + 24h PnL change.
   - Card 2: Open Positions (count) + Total Margin Used.
   - Card 3: Win Rate / Realized PnL (all-time).
   - Card 4: Bot Health Indicators (AssetTrade, PolyFollow, ForexPaper pills).

3. **Charts Section**:
   - Equity Growth Curve (Line chart with fill gradient).
   - Timeframe toggles: 24H, 7D, 30D, All.

4. **Positions & Recent Trades Table**:
   - Filter tabs: `[All]`, `[Crypto Futures]`, `[Polymarket]`, `[Forex]`.
   - Cards view on mobile, compact table on desktop.
   - Badges for Side (LONG/SHORT) and Risk R.

5. **Quick Controls & Emergency Panel (Bottom Drawer / Collapsible)**:
   - Panic Buttons with 2-step slider or confirmation modal.

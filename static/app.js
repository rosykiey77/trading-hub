// Trading Hub SPA (Alpine.js component)
function hub() {
  return {
    authed: true, password: '', loginError: '', busy: false, online: false, pulse: false,
    total: {}, bots: [], positions: [], actions: [], tab: '',
    chartBot: 'total', chartRange: '7d', chartEmpty: true, chart: null,
    clockWib: '', clockUtc: '', confirmAction: null, confirmText: '', actionMsg: '', actionOk: false,
    controls: [
      {label: 'Emergency Stop Forex', desc: 'Create STOP file: bot flattens all positions and shuts down.', url: '/api/control/forex/stop', danger: true},
      {label: 'Pause Futures', desc: 'Queue pause command on AssetTrade runner.', url: '/api/control/futures/pause', danger: true},
      {label: 'Resume Futures', desc: 'Queue resume command on AssetTrade runner.', url: '/api/control/futures/resume'},
      {label: 'Pause Copy-Trading', desc: 'Pause PolyFollow paper engine job (Hermes cron).', url: '/api/control/polymarket/pause', danger: true},
      {label: 'Resume Copy-Trading', desc: 'Resume PolyFollow paper engine job.', url: '/api/control/polymarket/resume'},
      {label: 'Restart AssetTrade Bot', desc: 'systemctl restart assettrade-bot@paper', url: '/api/control/restart/assettrade-bot'},
      {label: 'Restart AssetTrade API', desc: 'systemctl restart assettrade-bot-api', url: '/api/control/restart/assettrade-api'},
      {label: 'Restart Forex Bot', desc: 'systemctl restart forex-paper', url: '/api/control/restart/forex-paper'},
      {label: 'Restart PolyFollow API', desc: 'docker restart polyfollow_api', url: '/api/control/restart/polyfollow-api'},
    ],

    init() {
      this.tick(); setInterval(() => this.tick(), 1000);
      this.refresh(); setInterval(() => this.authed && this.refresh(), 15000);
      this.$watch('authed', () => this.$nextTick(() => lucide.createIcons()));
      lucide.createIcons();
    },
    tick() {
      const d = new Date(), f = tz => d.toLocaleTimeString('en-GB', {timeZone: tz});
      this.clockWib = f('Asia/Jakarta'); this.clockUtc = f('UTC');
    },
    async api(url, opts = {}) {
      const r = await fetch(url, {credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, ...opts});
      if (r.status === 401 && url !== '/api/login') { this.authed = false; throw new Error('auth'); }
      const body = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(body.detail || r.statusText);
      return body;
    },
    async login() {
      this.busy = true; this.loginError = '';
      try { await this.api('/api/login', {method: 'POST', body: JSON.stringify({password: this.password})}); this.password = ''; this.authed = true; this.refresh(); }
      catch (e) { this.loginError = 'Invalid password'; }
      this.busy = false;
    },
    async logout() { await this.api('/api/logout', {method: 'POST'}).catch(() => {}); this.authed = false; },
    async refresh() {
      try {
        const [o, p, a] = await Promise.all([this.api('/api/overview'), this.api('/api/positions'), this.api('/api/actions')]);
        if (this.total.equity !== undefined && this.total.equity !== o.total.equity) { this.pulse = true; setTimeout(() => this.pulse = false, 1200); }
        this.total = o.total; this.bots = o.bots; this.positions = p; this.actions = a; this.online = true;
        this.authed = true; this.loadChart();
      } catch (e) { if (e.message !== 'auth') this.online = false; }
    },
    async loadChart() {
      const pts = await this.api(`/api/equity?bot=${this.chartBot}&range=${this.chartRange}`).catch(() => []);
      this.chartEmpty = pts.length === 0;
      const el = document.getElementById('equityChart'), ctx = el.getContext('2d');
      const colors = {total: '#34d399', futures: '#22d3ee', polymarket: '#c084fc', forex: '#fbbf24'};
      const c = colors[this.chartBot], g = ctx.createLinearGradient(0, 0, 0, el.clientHeight || 280);
      g.addColorStop(0, c + '55'); g.addColorStop(1, c + '00');
      const labels = pts.map(p => new Date(p.t * 1000).toLocaleString('en-GB', {month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit'}));
      const data = pts.map(p => p.equity);
      if (this.chart) this.chart.destroy();
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {labels, datasets: [{data, borderColor: c, backgroundColor: g, fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2}]},
        options: {responsive: true, maintainAspectRatio: false, animation: false, interaction: {intersect: false, mode: 'index'},
          plugins: {legend: {display: false}, tooltip: {callbacks: {label: i => this.usd(i.parsed.y)}}},
          scales: {x: {ticks: {color: '#64748b', maxTicksLimit: 6}, grid: {color: '#1e293b'}},
                   y: {ticks: {color: '#64748b', callback: v => '$' + v.toLocaleString()}, grid: {color: '#1e293b'}}}},
      });
    },
    async runAction() {
      this.busy = true; this.actionMsg = '';
      try { const r = await this.api(this.confirmAction.url, {method: 'POST'}); this.actionOk = true; this.actionMsg = r.message || 'done'; }
      catch (e) { this.actionOk = false; this.actionMsg = e.message; }
      this.busy = false; this.confirmText = ''; this.refresh();
      setTimeout(() => { if (this.actionOk) this.confirmAction = null; this.actionMsg = ''; }, 2500);
    },
    filtered() { return this.positions.filter(p => !this.tab || p.platform === this.tab); },
    usd(v) { return v == null ? '–' : '$' + Number(v).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}); },
    signed(v) { return v == null ? '–' : (v >= 0 ? '+' : '-') + '$' + Math.abs(v).toFixed(2); },
    pct(v) { return v == null ? '–' : (v >= 0 ? '+' : '') + Number(v).toFixed(2) + '%'; },
    num(v) { return v == null ? '–' : String(parseFloat(Number(v).toPrecision(6))); },
    cls(v) { return v == null || v === 0 ? 'text-slate-300' : v > 0 ? 'text-emerald-400' : 'text-rose-400'; },
    color(b) { return {futures: 'text-cyan-400', polymarket: 'text-purple-400', forex: 'text-amber-400'}[b]; },
    short(b) { return {futures: 'Futures', polymarket: 'Poly', forex: 'Forex'}[b]; },
    pill(h) { return {green: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', yellow: 'bg-amber-500/10 text-amber-400 border-amber-500/30', red: 'bg-rose-500/10 text-rose-400 border-rose-500/30'}[h]; },
    side(s) { const l = ['LONG', 'BUY', 'UP', 'YES'].includes(String(s).toUpperCase()); const sh = ['SHORT', 'SELL', 'DOWN', 'NO'].includes(String(s).toUpperCase());
      return l ? 'bg-emerald-500/10 text-emerald-400' : sh ? 'bg-rose-500/10 text-rose-400' : 'bg-purple-500/10 text-purple-300'; },
    age(t) { if (!t) return ''; const s = (Date.now() - new Date(t).getTime()) / 1000;
      return s < 3600 ? Math.round(s / 60) + 'm' : s < 86400 ? (s / 3600).toFixed(1) + 'h' : (s / 86400).toFixed(1) + 'd'; },
  };
}

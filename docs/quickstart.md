# Quickstart / Validation

```bash
cd /home/ubuntu/trading-hub
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env   # set DASHBOARD_PASSWORD, SECRET_KEY, ASSETTRADE_API_KEY
.venv/bin/pytest -q    # expect all pass
sudo cp deploy/trading-hub.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now trading-hub
curl -s localhost:8200/health                       # {"ok":true}
curl -s -o /dev/null -w '%{http_code}' localhost:8200/api/overview   # 401
```

Browser: `http://<vps-ip>:8200` → log in → KPI cards, 3 health pills, positions, chart.
Contracts: [contracts/api.md](contracts/api.md). Entities: [data-model.md](data-model.md).

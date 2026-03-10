# Finpop Backend

FastAPI backend for the Order Alert mobile app.

## Structure

```
finpop-backend/
├── main.py                  ← FastAPI app, router mounts, lifespan
├── requirements.txt
├── .env.example             ← copy to .env and fill keys
│
├── core/
│   ├── database.py          ← SQLite: all tables + queries
│   ├── kite.py              ← Kite Connect wrapper (holdings/orders/margins/quotes)
│   ├── rule_engine.py       ← Rule evaluation + Claude NL parser + push sender
│   ├── scheduler.py         ← APScheduler: rule check (60s) + portfolio broadcast (30s)
│   └── ws_manager.py        ← WebSocket connection manager
│
└── routers/
    ├── auth.py              ← Kite OAuth login flow
    ├── portfolio.py         ← Holdings, orders, margins, snapshot
    ├── rules.py             ← CRUD + NL parse + preset conditions + dry-run test
    ├── alerts.py            ← Alert history
    ├── push.py              ← Expo push token registration
    └── websocket.py         ← WS /ws/portfolio — live portfolio stream
```

---

## Setup (5 minutes)

### 1. Create virtual environment

```bash
cd finpop-backend
python -m venv venv

# Windows (PowerShell)
.\venv\bin\Activate.ps1

# Mac / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your Kite API Key + Secret + Anthropic key
```

### 4. Start the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Your mobile app at `10.57.170.125:8081` can now reach the backend at `10.57.170.125:8000`.

---

## First Login (Kite OAuth)

```bash
# Step 1 — get the login URL
curl "http://localhost:8000/api/auth/login-url?api_key=YOUR_API_KEY"
# → {"url": "https://kite.zerodha.com/connect/login?api_key=..."}

# Step 2 — open that URL in browser → login to Zerodha
# → Browser redirects to your redirect_url with ?request_token=XXXX

# Step 3 — exchange for access token
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "request_token": "TOKEN_FROM_REDIRECT"
  }'
# → {"status":"authenticated","user_name":"Priyanka",...}
```

**Note:** Access tokens expire every day at 6am IST. You'll need to re-login each trading day.

---

## API Reference

### Auth

| Method | Path                           | Description                           |
| ------ | ------------------------------ | ------------------------------------- |
| GET    | `/api/auth/login-url?api_key=` | Get Zerodha OAuth URL                 |
| POST   | `/api/auth/token`              | Exchange request_token → access_token |
| GET    | `/api/auth/status`             | Check if logged in                    |
| DELETE | `/api/auth/logout`             | Log out                               |

### Portfolio

| Method | Path                                            | Description                             |
| ------ | ----------------------------------------------- | --------------------------------------- |
| GET    | `/api/portfolio/snapshot`                       | Holdings + orders + margins in one call |
| GET    | `/api/portfolio/holdings`                       | Long-term holdings                      |
| GET    | `/api/portfolio/orders`                         | Today's orders                          |
| GET    | `/api/portfolio/margins`                        | Account balance + margins               |
| GET    | `/api/portfolio/quote?instruments=NSE:NIFTY 50` | Live quote                              |

### Rules

| Method | Path                           | Description                          |
| ------ | ------------------------------ | ------------------------------------ |
| GET    | `/api/rules/preset-conditions` | List of preset condition types       |
| POST   | `/api/rules/parse`             | Plain English → JSON rule via Claude |
| POST   | `/api/rules`                   | Save a rule                          |
| GET    | `/api/rules`                   | List all rules                       |
| DELETE | `/api/rules/{id}`              | Delete a rule                        |
| POST   | `/api/rules/{id}/reset`        | Re-arm triggered rule                |
| POST   | `/api/rules/{id}/test`         | Dry-run against live price           |

### Alerts & Push

| Method | Path                  | Description              |
| ------ | --------------------- | ------------------------ |
| GET    | `/api/alerts/history` | Triggered alert log      |
| POST   | `/api/push/register`  | Register Expo push token |

### WebSocket

```
ws://10.57.170.125:8000/ws/portfolio
```

Receives JSON messages:

```json
{"type": "portfolio_update", "holdings": [...], "margins": {...}}
{"type": "alert_triggered",  "rule_id": 1, "instrument": "NSE:NIFTY 50", "price": 22100}
{"type": "pong"}
```

---

## Connecting from React Native

```js
// services/api.js — already set to your IP
export const API_BASE = "http://10.57.170.125:8000";

// WebSocket connection (add to a useEffect in your app)
const ws = new WebSocket("ws://10.57.170.125:8000/ws/portfolio");

ws.onopen = () => console.log("Connected");
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === "portfolio_update") {
    setHoldings(data.holdings);
    setMargins(data.margins);
  }
};
ws.onclose = () => console.log("Disconnected");
```

---

## Dev Mode (no Kite API key yet)

The backend runs fine without Kite credentials — it returns realistic mock data for holdings, orders, and margins so you can develop the full UI first. Mock mode is auto-detected when no access token is present.

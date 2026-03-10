# 📱 Order Alert — React Native (Expo) App

## Project Structure

```
rn-alert-app/
├── App.js                        ← Root: navigation + push notification setup
├── app.json                      ← Expo config
├── package.json
├── theme.js                      ← Colors, fonts, shared constants
├── services/
│   ├── api.js                    ← All backend API calls
│   └── notifications.js          ← Expo push notification registration
├── screens/
│   ├── AddRuleScreen.js          ← Type plain English → Claude parses → save
│   ├── RulesScreen.js            ← List rules, test, reset, delete
│   └── HistoryScreen.js          ← Triggered alert log
└── push_service.py               ← Drop into your Python backend
```

---

## ⚡ Setup

### 1. Install dependencies

```bash
cd rn-alert-app
npm install
```

### 2. Point the app at your backend

Edit `services/api.js` — change `API_BASE` to your machine's local IP:

```js
// Not localhost — use your actual LAN IP so the phone can reach it
export const API_BASE = "http://192.168.1.10:8000";
```

Or set it in `app.json`:
```json
"extra": { "apiBaseUrl": "http://192.168.1.10:8000" }
```

> Find your IP: `ipconfig` (Windows) or `ifconfig | grep inet` (Mac/Linux)

### 3. Start the app

```bash
npx expo start
```

Scan the QR code with the **Expo Go** app on your phone.

---

## 🔔 Push Notifications Setup

### Step 1 — Add push_service.py to your backend

Copy `push_service.py` into your `backend/` folder, then edit `main.py`:

```python
from push_service import init_push_table, save_push_token, send_push_notification
from pydantic import BaseModel

class PushTokenRequest(BaseModel):
    token: str

# In startup():
init_push_table()

# New route:
@app.post("/api/push/register")
async def register_push_token(req: PushTokenRequest):
    save_push_token(req.token)
    return {"status": "registered"}
```

### Step 2 — Fire push from rule_engine.py

In `rule_engine.py`, inside `_fire_alert()`:

```python
import asyncio
from push_service import send_push_notification

# Add after send_notification():
asyncio.run(send_push_notification(
    title=f"🚨 {instrument}",
    body=description
))
```

### Step 3 — Physical device required

Push notifications only work on a **real device**, not the simulator.
Use `npx expo start --tunnel` if your phone and laptop are on different networks.

### Step 4 — Get your Expo project ID

1. Run `npx expo login`
2. Run `npx expo init` or create a project at expo.dev
3. Paste the project ID into `services/notifications.js`:
   ```js
   projectId: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   ```

---

## 📲 Screens

| Screen | What it does |
|--------|-------------|
| Rules | Lists all rules with status badges. Tap Test to dry-run. Tap Reset to re-arm a triggered rule. Pull to refresh. |
| Add Rule | Type a plain-English alert. Tap "Parse with Claude" to convert it to a structured rule. Review and save. |
| History | Grouped chronological log of all triggered alerts with instrument, price, and time. |

---

## 🏗 Building for Production

```bash
# Install EAS CLI
npm install -g eas-cli
eas login

# Configure build
eas build:configure

# Build for Android (APK)
eas build --platform android --profile preview

# Build for iOS (requires Apple Developer account)
eas build --platform ios
```

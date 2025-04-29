# final_again

## Project Map & Architecture

This repository contains two Python scripts under `sports bot/football bot/`:
- **websocket.py**  
  Connects over MQTT via WebSocket + TLS to `mq.thesports.com` on topic `thesports/football/match/v1`.
- **live.py**  
  Periodically polls a sports‐data REST API (every 2 s by default), logs raw JSON and extracts score, stats, and incidents.

---

## 1. React Front-end

1. **Define data pipeline & requirements**  
   - **Endpoints**  
     - `/football/match/recent/list` → get match IDs  
     - `/football/match/detail_live` → live scores & stats  
     - (Optional) odds, team info, competition info…  
   - **Refresh intervals**  
     - Live detail: every 2 s  
     - Static team/competition data: less frequent  
   - **Model**  
     - Final JSON shape for front-end consumption  

2. **Sketch front-end flow**  
   - HTTP polling or WebSocket for real-time updates  
   - Components (e.g. `<MatchCard>` to render one match object)

---

## 2. Python / FastAPI Backend

### 2.1. Set up project

```bash
mkdir sports-api && cd sports-api
python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn httpx
```

### 2.2. Implement fetch helpers

```python
from httpx import AsyncClient

client = AsyncClient()

async def fetch_recent():
    r = await client.get(RECENT_LIST_URL, params={…})
    return r.json()

async def fetch_detail(match_id):
    r = await client.get(DETAIL_LIVE_URL, params={"id": match_id})
    return r.json()
```

### 2.3. Define `/live-matches` endpoint

```python
@app.get("/live-matches")
async def live_matches():
    rec = await fetch_recent()
    ids = [m["id"] for m in rec["results"]]
    details = await asyncio.gather(*(fetch_detail(i) for i in ids))
    # merge/filter into your schema…
    return details
```

### 2.4. Handle CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_methods=["GET","POST"],
  allow_headers=["*"],
)
```

### 2.5. (Optional) WebSocket endpoint

```python
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        await ws.send_json(await get_live_data())
        await asyncio.sleep(2)
```

---

## 3. Test & Optimize Backend

- Run locally:  
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```
- Verify with Postman or `curl http://localhost:8000/live-matches`  
- Add caching (in-memory or Redis) for static data  
- Implement logging & error handling for timeouts  

---

## 4. Scaffold React Front-end

```bash
npm create vite@latest sports-ui --template react
cd sports-ui
npm install
npm run dev
```

### 4.1. HTTP polling

```js
useEffect(() => {
  const fetchLive = async () => {
    const resp = await fetch("http://localhost:8000/live-matches");
    setMatches(await resp.json());
  };
  fetchLive();
  const id = setInterval(fetchLive, 2000);
  return () => clearInterval(id);
}, []);
```

### 4.2. WebSocket (instant updates)

```js
useEffect(() => {
  const ws = new WebSocket("ws://localhost:8000/ws");
  ws.onmessage = e => setMatches(JSON.parse(e.data));
  return () => ws.close();
}, []);
```

Render matches in a list or grid, displaying score, minute, stats, incidents.

---

## 5. Polish & Deploy

- **Styling & UX**: spinners, error banners, debounce/throttle  
- **Build & serve** React (e.g. `npm run build`) behind Nginx or Vercel  
- **Containerization**: Docker + docker‐compose for API + UI  
- **TLS/WebSocket Secure**: use `wss://` and HTTPS in production  
- **Monitoring**: health checks, logs, metrics  

---

**Next Steps**  
1. Validate each endpoint and component.  
2. Integrate front-end with backend.  
3. Deploy to staging, then production.  
4. Secure credentials and enable caching for performance.  

Good luck!

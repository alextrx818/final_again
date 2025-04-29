import asyncio
import aiohttp
import time
import json
from pathlib import Path
from live import fetch_live_match  # fetches live matches with "id" fields

# ─── Credentials ────────────────────────────────────────────────────────────
USER   = "thenecpt"
SECRET = "0c55322e8e1966ef9066fa4252cf386"

# ─── Endpoints ──────────────────────────────────────────────────────────────
RECENT_URL = "https://api.thesports.com/v1/football/match/recent/list"
DETAIL_URL = "https://api.thesports.com/v1/football/match/detail_live"

# ─── State ──────────────────────────────────────────────────────────────────
STATE_DIR = Path(__file__).parent / "state"
STATE_DIR.mkdir(exist_ok=True)

def load_state(match_id: str) -> dict:
    path = STATE_DIR / f"{match_id}.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return {}
    return {}

def save_state(match_id: str, state: dict):
    path = STATE_DIR / f"{match_id}.json"
    path.write_text(json.dumps(state))

async def fetch_recent_list(session: aiohttp.ClientSession, uuid: str, since: int = None) -> list:
    params = {"user": USER, "secret": SECRET, "uuid": uuid}
    if since:
        params["time"] = since
    async with session.get(RECENT_URL, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()
    return data.get("results", [])

async def full_update(session: aiohttp.ClientSession, uuid: str) -> list:
    # For a specific match UUID, only one page of data is returned
    results = await fetch_recent_list(session, uuid)
    print(f"Fetched full recent list for {uuid}: {len(results)} records")
    ts = int(time.time())
    save_state(uuid, {"last_update": ts})
    return results

async def incremental_update(session: aiohttp.ClientSession, uuid: str) -> list:
    state = load_state(uuid)
    last = state.get("last_update")
    if not last:
        return await full_update(session, uuid)
    results = await fetch_recent_list(session, uuid, since=last)
    print(f"Fetched incremental recent list for {uuid} since {last}: {len(results)} records")
    ts = int(time.time())
    save_state(uuid, {"last_update": ts})
    return results

async def fetch_match_detail(session: aiohttp.ClientSession, uuid: str) -> dict:
    params = {"user": USER, "secret": SECRET, "uuid": uuid}
    async with session.get(DETAIL_URL, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()

def find_team_ids(data) -> list:
    ids = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k in ("home_team", "away_team") and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
            else:
                ids.extend(find_team_ids(v))
    elif isinstance(data, list):
        for item in data:
            ids.extend(find_team_ids(item))
    return ids

async def process_match(uuid: str):
    async with aiohttp.ClientSession() as session:
        state = load_state(uuid)
        if not state.get("last_update"):
            recents = await full_update(session, uuid)
        else:
            recents = await incremental_update(session, uuid)

        print(f"Total recent records for {uuid}: {len(recents)}")

        detail = await fetch_match_detail(session, uuid)
        print(f"\n🔄 Detail for match {uuid}:")
        print(json.dumps(detail, indent=2))

        team_ids = find_team_ids(detail)
        if team_ids:
            print(f"🔎 Found team IDs: {team_ids}")

async def main():
    live = await asyncio.to_thread(fetch_live_match)
    match_ids = [m.get("id") for m in live.get("results", []) if m.get("id")]
    if not match_ids:
        print("No live matches.")
        return
    for mid in match_ids:
        await process_match(mid)

if __name__ == "__main__":
    asyncio.run(main())

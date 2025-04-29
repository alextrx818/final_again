import asyncio
import aiohttp
import time
import json
from pathlib import Path
from live import fetch_live_match  # fetches live matches with "id" fields

# ─── Credentials ────────────────────────────────────────────────────────────
USER   = "thenecpt"
SECRET = "0c55322e8e196d6ef9066fa4252cf386"

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


async def fetch_recent_list(session: aiohttp.ClientSession, uuid: str, page: int = 1, since: int = None) -> dict:
    params = {"user": USER, "secret": SECRET, "uuid": uuid, "page": page}
    if since:
        params["time"] = since
    async with session.get(RECENT_URL, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


async def full_update(session: aiohttp.ClientSession, uuid: str) -> list:
    results = []
    page = 1
    while True:
        data = await fetch_recent_list(session, uuid, page)
        page_data = data.get("results", [])
        if not page_data:
            break
        print(f"Fetched full page {page} for {uuid}: {len(page_data)} records")
        results.extend(page_data)
        page += 1
    ts = int(time.time())
    save_state(uuid, {"last_update": ts})
    return results


async def incremental_update(session: aiohttp.ClientSession, uuid: str) -> list:
    state = load_state(uuid)
    last = state.get("last_update")
    if not last:
        return await full_update(session, uuid)
    data = await fetch_recent_list(session, uuid, page=1, since=last)
    inc = data.get("results", [])
    print(f"Fetched incremental for {uuid} since {last}: {len(inc)} records")
    ts = int(time.time())
    save_state(uuid, {"last_update": ts})
    return inc


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
            print(f"Full update for match {uuid}")
            recents = await full_update(session, uuid)
        else:
            print(f"Incremental update for match {uuid}")
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
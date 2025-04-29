import time
import json
import requests

# ─── Configuration ─────────────────────────────────────────────────────────────
USER     = "thenecpt"
SECRET   = "0c55322e8e196d6ef9066fa4252cf386"
URL      = "https://api.thesports.com/v1/football/match/detail_live"
INTERVAL = 2  # seconds between requests

def calculate_match_minute(now_ts, kickoff_ts, is_second_half):
    """
    Calculate the current match minute.
    First half: (now - kickoff_first) / 60 + 1
    Second half: (now - kickoff_second) / 60 + 45 + 1
    """
    minutes = int((now_ts - kickoff_ts) / 60) + 1
    if is_second_half:
        minutes += 45
    return minutes

def fetch_live_match():
    try:
        response = requests.get(URL,
                                params={"user": USER, "secret": SECRET},
                                timeout=10)
        response.raise_for_status()
        data = response.json()
        print("Raw data:", json.dumps(data, indent=2))

        now_ts = int(time.time())
        # Determine which kickoff timestamp to use
        kickoff_first  = data.get("kickoff_first", 0)
        kickoff_second = data.get("kickoff_second", 0)
        is_second_half = now_ts >= kickoff_second and kickoff_second > 0

        kickoff_ts = kickoff_second if is_second_half else kickoff_first
        match_min    = calculate_match_minute(now_ts, kickoff_ts, is_second_half)

        print(f"\nMatch minute: {match_min}")
        # Print score
        print("Score:")
        score = data.get("score", {})
        print(score)

        # Print incidents
        print("Incidents:")
        for incident in data.get("incidents", []):
            print(incident)

        # Print technical statistics
        print("Statistics:")
        for stat in data.get("stats", []):
            print(stat)

    except Exception as e:
        print(f"Error fetching live match data at {time.strftime('%H:%M:%S')}: {e}")

def main():
    print(f"Starting live match polling every {INTERVAL} seconds...")
    while True:
        fetch_live_match()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()

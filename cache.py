import os
import csv
import requests

API_KEY = "1a5255100fec5a5c00d79e25b4d26b67"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

CACHE_DIR = "data/cache"

os.makedirs(CACHE_DIR, exist_ok=True)

def guardar_partidos_csv(team_id, league_id, season):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "league": league_id, "season": season}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    data = r.json().get("response", [])

    ruta = os.path.join(CACHE_DIR, f"partidos_{team_id}_{season}.csv")

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "fecha", "home", "away",
            "gol_home", "gol_away"
        ])

        for p in data:
            fixture = p.get("fixture", {})
            teams = p.get("teams", {})
            goals = p.get("goals", {})

            writer.writerow([
                fixture.get("date", ""),
                teams.get("home", {}).get("name", ""),
                teams.get("away", {}).get("name", ""),
                goals.get("home", 0),
                goals.get("away", 0),
            ])

    return ruta

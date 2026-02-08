import requests

API_KEY = "1a5255100fec5a5c00d79e25b4d26b67"

def obtener_stats_equipo(league_id, season, team_id):
    url = "https://v3.football.api-sports.io/teams/statistics"
    headers = {"x-apisports-key": API_KEY}
    params = {
        "league": league_id,
        "season": season,
        "team": team_id
    }

    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    return data["response"]

# EJEMPLO: Premier League, temporada 2024, Manchester United (team_id=33)
stats = obtener_stats_equipo(39, 2024, 33)

print("Partidos jugados:", stats["fixtures"]["played"]["total"])
print("Goles a favor:", stats["goals"]["for"]["total"]["total"])
print("Goles en contra:", stats["goals"]["against"]["total"]["total"])

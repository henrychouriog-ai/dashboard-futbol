import requests

API_KEY = "1f68791bbac447a1ab9fb866f58a4326"
BASE_URL = "https://api.football-data.org/v4"

HEADERS = {
    "X-Auth-Token": API_KEY
}

# =========================
# Ligas
# =========================
def obtener_ligas():
    url = f"{BASE_URL}/competitions"
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return []

    data = r.json()
    ligas = []
    for c in data.get("competitions", []):
        ligas.append({
            "id": c["id"],
            "nombre": c["name"],
            "pais": c["area"]["name"]
        })
    return ligas

# =========================
# Equipos por liga
# =========================
def obtener_equipos_liga(league_id):
    url = f"{BASE_URL}/competitions/{league_id}/teams"
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return []

    data = r.json()
    equipos = []
    for t in data.get("teams", []):
        equipos.append({
            "id": t["id"],
            "nombre": t["name"]
        })
    return equipos

# =========================
# Partidos de un equipo
# =========================
def obtener_partidos_equipo(team_id, limit=10):
    url = f"{BASE_URL}/teams/{team_id}/matches"
    params = {"limit": limit, "status": "FINISHED"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    if r.status_code != 200:
        return {}

    return r.json()

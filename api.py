import os
import time
import json
import requests
import pandas as pd

# =========================
# CONFIG
# =========================
API_KEY = "1a5255100fec5a5c00d79e25b4d26b67"
BASE_URL = "https://v3.football.api-sports.io"
CACHE_DIR = "cache"
CACHE_HORAS = 12  # 2 veces al día

os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "x-apisports-key": API_KEY
}

# =========================
# Utils cache
# =========================
def _cache_path(nombre):
    return os.path.join(CACHE_DIR, nombre)

def _cache_valido(path):
    if not os.path.exists(path):
        return False
    edad = time.time() - os.path.getmtime(path)
    return edad < CACHE_HORAS * 3600

def _leer_cache(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _guardar_cache(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _api_get(endpoint, params=None):
    url = BASE_URL + endpoint
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# =========================
# API FUNCTIONS (MISMA INTERFAZ)
# =========================
def obtener_ligas():
    cache_file = _cache_path("ligas.json")

    if _cache_valido(cache_file):
        return _leer_cache(cache_file)

    data = _api_get("/leagues")
    ligas = []
    for l in data.get("response", []):
        ligas.append({
            "id": l["league"]["id"],
            "nombre": l["league"]["name"],
            "pais": l["country"]["name"] if l.get("country") else ""
        })

    _guardar_cache(cache_file, ligas)
    return ligas


def obtener_equipos_liga(league_id, season):
    cache_file = _cache_path(f"equipos_{league_id}_{season}.json")

    if _cache_valido(cache_file):
        return _leer_cache(cache_file)

    data = _api_get("/teams", params={"league": league_id, "season": season})
    equipos = []
    for t in data.get("response", []):
        equipos.append({
            "id": t["team"]["id"],
            "nombre": t["team"]["name"]
        })

    _guardar_cache(cache_file, equipos)
    return equipos


def obtener_partidos_con_cache(team_id, league_id, season):
    cache_file = _cache_path(f"partidos_{team_id}_{league_id}_{season}.csv")

    # Si cache válido → leer CSV
    if _cache_valido(cache_file):
        try:
            return pd.read_csv(cache_file)
        except:
            pass  # si falla, vuelve a pedir a la API

    # Llamada API
    data = _api_get("/fixtures", params={
        "team": team_id,
        "league": league_id,
        "season": season
    })

    filas = []
    for f in data.get("response", []):
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]
        gh = f["goals"]["home"]
        ga = f["goals"]["away"]

        if gh is None or ga is None:
            continue

        filas.append({
            "home": home,
            "away": away,
            "gol_home": gh,
            "gol_away": ga
        })

    df = pd.DataFrame(filas)

    # Guardar cache
    if not df.empty:
        df.to_csv(cache_file, index=False)

    return df














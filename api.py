import os
import json
import requests
import streamlit as st

# =========================
# CONFIGURACIÓN
# =========================
def obtener_api_key():
    try:
        return st.secrets["general"]["api_key"]
    except:
        return "TU_API_KEY_AQUI" 

BASE_URL = "https://v3.football.api-sports.io"
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _api_get(endpoint, params=None):
    key = obtener_api_key()
    headers = {"x-apisports-key": key, "Content-Type": "application/json"}
    try:
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"response": []}

# --- FUNCIONES EXISTENTES ---

def obtener_ligas():
    cache_path = os.path.join(CACHE_DIR, "ligas_cache.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f: return json.load(f)
    data = _api_get("/leagues")
    ligas = []
    for l in data.get("response", []):
        ligas.append({
            "id": l["league"]["id"],
            "nombre": f"{l['country']['name']} - {l['league']['name']}",
            "logo": l["league"]["logo"],
            "solo_nombre": l["league"]["name"]
        })
    if ligas:
        with open(cache_path, "w") as f: json.dump(ligas, f)
    return ligas

def obtener_equipos_liga(league_id):
    cache_path = os.path.join(CACHE_DIR, f"equipos_{league_id}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f: return json.load(f)
    data = _api_get("/teams", params={"league": league_id, "season": 2024})
    equipos = []
    for t in data.get("response", []):
        equipos.append({"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]})
    if equipos:
        with open(cache_path, "w") as f: json.dump(equipos, f)
    return equipos

def obtener_promedios_goles(team_id, league_id):
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2024, "last": 15})
    g_f, g_c, p = 0, 0, 0
    responses = data.get("response", [])
    if not responses: return (1.20, 1.10)
    for f in responses:
        gh, ga = f["goals"]["home"], f["goals"]["away"]
        if gh is None or ga is None: continue
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.20, 1.10)

# --- ESTA ES LA FUNCIÓN QUE TE DABA EL ERROR (AGRÉGALA) ---
def obtener_h2h(id_local, id_visitante):
    h2h_query = f"{id_local}-{id_visitante}"
    data = _api_get("/fixtures/headtohead", params={"h2h": h2h_query, "last": 5})
    
    resultados = []
    for f in data.get("response", []):
        gh, ga = f["goals"]["home"], f["goals"]["away"]
        ganador = "Empate"
        if gh > ga: ganador = f["teams"]["home"]["name"]
        elif ga > gh: ganador = f["teams"]["away"]["name"]
        
        resultados.append({
            "fecha": f["fixture"]["date"][:10],
            "marcador": f"{gh}-{ga}",
            "ganador": ganador
        })
    return resultados

def limpiar_cache_completo():
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            os.remove(os.path.join(CACHE_DIR, f))














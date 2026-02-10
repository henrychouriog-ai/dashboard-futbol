import os
import time
import json
import requests
import streamlit as st

# =========================
# CONFIGURACIÓN
# =========================
def obtener_api_key():
    # Intenta obtenerla de Streamlit Secrets o ponla aquí directamente entre comillas
    try:
        return st.secrets["general"]["api_key"]
    except:
        return "TU_API_KEY_AQUI" 

BASE_URL = "https://v3.football.api-sports.io"
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# --- Función de limpieza para el usuario ---
def limpiar_cache_completo():
    for f in os.listdir(CACHE_DIR):
        os.remove(os.path.join(CACHE_DIR, f))

# --- Motor de peticiones ---
def _api_get(endpoint, params=None):
    key = obtener_api_key()
    headers = {"x-apisports-key": key, "Content-Type": "application/json"}
    try:
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=7)
        return r.json()
    except Exception as e:
        print(f"Error de conexión: {e}")
        return {"response": []}

# =========================
# FUNCIONES OPTIMIZADAS
# =========================

def obtener_ligas():
    # Usamos caché para que el selector sea instantáneo
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
            "solo_nombre": l["league"]["name"],
            "pais": l["country"]["name"]
        })
    
    if ligas:
        with open(cache_path, "w") as f: json.dump(ligas, f)
    return ligas

def obtener_equipos_liga(league_id):
    # Evitamos llamadas repetitivas
    cache_path = os.path.join(CACHE_DIR, f"equipos_{league_id}.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f: return json.load(f)

    # Usamos 2025 directamente para ganar velocidad
    data = _api_get("/teams", params={"league": league_id, "season": 2025})
    
    # Si 2025 no tiene datos, intentamos 2024 automáticamente
    if not data.get("response"):
        data = _api_get("/teams", params={"league": league_id, "season": 2024})

    equipos = []
    for t in data.get("response", []):
        equipos.append({
            "id": t["team"]["id"], 
            "nombre": t["team"]["name"],
            "logo": t["team"]["logo"]
        })
    
    if equipos:
        with open(cache_path, "w") as f: json.dump(equipos, f)
    return equipos

def obtener_promedios_goles(team_id, league_id):
    # Intentamos obtener los últimos 10 partidos para las métricas
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2025, "last": 10})
    
    # Si 2025 está vacío, probamos 2024
    if not data.get("response"):
        data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2024, "last": 10})

    g_f, g_c, p = 0, 0, 0
    responses = data.get("response", [])
    
    if not responses:
        return (1.55, 1.25) # Datos de relleno para que no se dañe la visual

    for f in responses:
        gh, ga = f["goals"]["home"], f["goals"]["away"]
        if gh is None or ga is None: continue
        
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.50, 1.20)














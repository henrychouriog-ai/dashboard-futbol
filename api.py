import requests
import streamlit as st
import time

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    try:
        if "general" in st.secrets and "api_key" in st.secrets["general"]:
            key = st.secrets["general"]["api_key"]
        else:
            return {"response": []}
            
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        if params is None: params = {}
        params["_t"] = int(time.time()) # Evita caché vieja
        
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except:
        return {"response": []}

@st.cache_data(ttl=600)
def obtener_ligas():
    # Volvemos a traer TODAS las ligas del mundo
    data = _api_get("/leagues")
    response = data.get("response", [])
    if not response:
        return [{"id": 140, "nombre": "La Liga (Spain)", "logo": "https://media.api-sports.io/football/leagues/140.png"}]
    
    lista = []
    for l in response:
        lista.append({
            "id": l["league"]["id"], 
            "nombre": f"{l['league']['name']} ({l['country']['name']})", 
            "logo": l["league"].get("logo", "")
        })
    return sorted(lista, key=lambda x: x['nombre'])

@st.cache_data(ttl=600)
def obtener_equipos_liga(league_id):
    # Intentamos 2025 (Temporada actual en 2026) y luego 2024
    for yr in [2025, 2024]:
        data = _api_get("/teams", params={"league": league_id, "season": yr})
        res = data.get("response", [])
        if res:
            return sorted([
                {"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
                for t in res
            ], key=lambda x: x['nombre'])
    return []

def obtener_promedios_goles(team_id, league_id):
    # Buscamos datos reales de los últimos 10 partidos
    for yr in [2025, 2024]:
        data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": yr, "last": 10})
        res = data.get("response", [])
        if res and len(res) >= 3:
            g_f, g_c, p = 0, 0, 0
            for f in res:
                gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
                if gh is not None and ga is not None:
                    if f["teams"]["home"]["id"] == team_id:
                        g_f += gh; g_c += ga
                    else:
                        g_f += ga; g_c += gh
                    p += 1
            if p > 0: return (round(g_f/p, 2), round(g_c/p, 2))
    return (1.45, 1.15) # Promedio base si no hay datos

def obtener_h2h(id_local, id_visitante):
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_local}-{id_visitante}", "last": 5})
    h2h_lista = []
    for f in data.get("response", []):
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is not None and ga is not None:
            ganador = "Empate"
            if gh > ga: ganador = f["teams"]["home"]["name"]
            elif ga > gh: ganador = f["teams"]["away"]["name"]
            h2h_lista.append({"Fecha": f["fixture"]["date"][:10], "Marcador": f"{gh}-{ga}", "Ganador": ganador})
    return h2h_lista















import requests
import streamlit as st

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    try:
        key = st.secrets["general"]["api_key"]
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except:
        return {"response": []}

@st.cache_data(ttl=3600)
def obtener_ligas():
    data = _api_get("/leagues")
    lista = []
    for l in data.get("response", []):
        lista.append({
            "id": l["league"]["id"], 
            "nombre": l["league"]["name"], 
            "logo": l["league"].get("logo", "")
        })
    return sorted(lista, key=lambda x: x['nombre'])

@st.cache_data(ttl=3600)
def obtener_temporada_actual(league_id):
    # Volvemos al 2024 que es la que te cargaba bien
    return 2024 

@st.cache_data(ttl=600)
def obtener_equipos_liga(league_id):
    # Intentamos 2024 y 2025 como respaldo
    for year in [2024, 2025]:
        data = _api_get("/teams", params={"league": league_id, "season": year})
        res = data.get("response", [])
        if res:
            return sorted([
                {"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
                for t in res
            ], key=lambda x: x['nombre'])
    return []

def obtener_promedios_goles(team_id, league_id):
    # Buscamos en la temporada 2024
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2024, "last": 10})
    res = data.get("response", [])
    
    if not res: return (1.45, 1.25)

    g_f, g_c, p = 0, 0, 0
    for f in res:
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is None or ga is None: continue
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.45, 1.25)

def obtener_h2h(id_local, id_visitante):
    # Versión mejorada: Busca en toda la historia para que NO salga vacío
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_local}-{id_visitante}", "last": 5})
    h2h_lista = []
    for f in data.get("response", []):
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is None or ga is None: continue
        ganador = "Empate"
        if gh > ga: ganador = f["teams"]["home"]["name"]
        elif ga > gh: ganador = f["teams"]["away"]["name"]
        h2h_lista.append({
            "Fecha": f["fixture"]["date"][:10], 
            "Marcador": f"{gh}-{ga}", 
            "Ganador": ganador
        })
    return h2h_lista















import requests
import streamlit as st

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    try:
        # Validación de seguridad para la Key
        if "general" not in st.secrets or "api_key" not in st.secrets["general"]:
            st.error("Falta la API Key en Secrets")
            return {"response": []}
            
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
    # FORZAMOS 2024: Esto evita el error de la pantalla negra
    return 2024 

@st.cache_data(ttl=600)
def obtener_equipos_liga(league_id):
    # Buscamos en 2024 que tiene datos confirmados
    data = _api_get("/teams", params={"league": league_id, "season": 2024})
    res = data.get("response", [])
    
    # Si 2024 falla, intentamos 2025
    if not res:
        data = _api_get("/teams", params={"league": league_id, "season": 2025})
        res = data.get("response", [])
        
    return sorted([
        {"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
        for t in res
    ], key=lambda x: x['nombre']) if res else []

def obtener_promedios_goles(team_id, league_id):
    # Siempre buscamos en temporadas con historial (2024)
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2024, "last": 10})
    res = data.get("response", [])
    
    if not res: return (1.40, 1.20)

    g_f, g_c, p = 0, 0, 0
    for f in res:
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is None or ga is None: continue
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.40, 1.20)

def obtener_h2h(id_local, id_visitante):
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_local}-{id_visitante}", "last": 5})
    h2h_lista = []
    for f in data.get("response", []):
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is None or ga is None: continue
        ganador = "Empate"
        if gh > ga: ganador = f["teams"]["home"]["name"]
        elif ga > gh: ganador = f["teams"]["away"]["name"]
        h2h_lista.append({"Fecha": f["fixture"]["date"][:10], "Marcador": f"{gh}-{ga}", "Ganador": ganador})
    return h2h_lista















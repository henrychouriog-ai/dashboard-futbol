import requests
import streamlit as st
import datetime

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    try:
        # Busca la clave en los Secrets de Streamlit
        key = st.secrets["general"]["api_key"]
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except Exception:
        return {"response": []}

@st.cache_data(ttl=3600)
def obtener_temporada_actual(league_id):
    """Detecta el año actual configurado para la liga en la API."""
    data = _api_get("/leagues", params={"id": league_id})
    for l in data.get("response", []):
        for s in l.get("seasons", []):
            if s.get("current"):
                return s.get("year")
    return datetime.datetime.now().year

@st.cache_data(ttl=3600)
def obtener_ligas():
    data = _api_get("/leagues")
    return [{"id": l["league"]["id"], "nombre": l["league"]["name"], "logo": l["league"]["logo"]} 
            for l in data.get("response", [])]

@st.cache_data(ttl=600)
def obtener_equipos_liga(league_id):
    year = obtener_temporada_actual(league_id)
    data = _api_get("/teams", params={"league": league_id, "season": year})
    # Si la temporada nueva no tiene equipos aún, intenta con la anterior
    if not data.get("response"):
        data = _api_get("/teams", params={"league": league_id, "season": year - 1})
    return sorted([{"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
                   for t in data.get("response", [])], key=lambda x: x['nombre'])

def obtener_promedios_goles(team_id, league_id):
    year = obtener_temporada_actual(league_id)
    # Buscamos los últimos 10 partidos para calcular promedios reales
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": year, "last": 10})
    res = data.get("response", [])
    
    # Si no hay datos en la actual, busca en la anterior (esencial para ligas que acaban de empezar)
    if len(res) < 2:
        data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": year - 1, "last": 10})
        res = data.get("response", [])

    if not res: return (1.30, 1.10) # Valores de seguridad si la API no responde nada

    g_f, g_c, p = 0, 0, 0
    for f in res:
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is None or ga is None: continue
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.30, 1.10)

def obtener_h2h(id_local, id_visitante):
    """Obtiene los últimos 5 enfrentamientos directos históricos."""
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














import requests
import streamlit as st

# NO usamos os ni json para evitar leer archivos viejos del servidor
BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    # Forzamos la lectura de la key desde Secrets
    key = st.secrets["general"]["api_key"]
    headers = {"x-apisports-key": key, "Content-Type": "application/json"}
    try:
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except:
        return {"response": []}

@st.cache_data(ttl=600) # Solo caché en memoria por 10 min
def obtener_ligas():
    data = _api_get("/leagues")
    return [{"id": l["league"]["id"], "nombre": l["league"]["name"], "logo": l["league"]["logo"]} 
            for l in data.get("response", [])]

@st.cache_data(ttl=600)
def obtener_equipos_liga(league_id):
    # Probamos 2024 que es la temporada con más datos estables ahora
    data = _api_get("/teams", params={"league": league_id, "season": 2024})
    return sorted([{"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
                   for t in data.get("response", [])], key=lambda x: x['nombre'])

def obtener_promedios_goles(team_id, league_id):
    # Si la API falla, devolveremos valores DISTINTOS para saber que no hay conexión
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2024, "last": 10})
    res = data.get("response", [])
    if not res: return (0.01, 0.01) # Si ves 0.01 es que la API no respondió

    g_f, g_c, p = 0, 0, 0
    for f in res:
        gh, ga = f["goals"]["home"], f["goals"]["away"]
        if gh is None or ga is None: continue
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (0.01, 0.01)

def obtener_h2h(id_local, id_visitante):
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_local}-{id_visitante}", "last": 5})
    return [{"Fecha": f["fixture"]["date"][:10], "Marcador": f"{f['goals']['home']}-{f['goals']['away']}", 
             "Ganador": "Local" if f['goals']['home'] > f['goals']['away'] else "Visita" if f['goals']['away'] > f['goals']['home'] else "Empate"} 
            for f in data.get("response", [])]














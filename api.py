import requests
import streamlit as st

# NO usamos os ni json para evitar leer archivos viejos del servidor
BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    # Forzamos la lectura de la key desde Secrets
    try:
        key = st.secrets["general"]["api_key"]
    except:
        return {"response": []} # Falla silenciosa si no hay key
        
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
    # Si la API falla, devolveremos 0.01 para saber que no hay conexión real
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2024, "last": 10})
    res = data.get("response", [])
    
    if not res: 
        return (0.01, 0.01)

    g_f, g_c, p = 0, 0, 0
    for f in res:
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is None or ga is None: continue
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (0.01, 0.01)

def obtener_h2h(id_local, id_visitante):
    # Buscamos enfrentamientos directos sin importar la liga
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
            "Equipos": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}",
            "Marcador": f"{gh}-{ga}",
            "Ganador": ganador
        })
    return h2h_lista














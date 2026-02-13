import requests
import streamlit as st
import time

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    try:
        # Intenta obtener la clave de los secrets de Streamlit
        key = st.secrets["general"]["api_key"]
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        # Agregamos un timestamp para evitar que la API nos devuelva datos viejos (cache)
        if params is None: params = {}
        params["v"] = int(time.time())
        
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Error de conexión: {e}")
        return {"response": []}

@st.cache_data(ttl=3600)
def obtener_ligas():
    data = _api_get("/leagues")
    res = data.get("response", [])
    if not res:
        # Ligas de respaldo si la API falla totalmente
        return [{"id": 140, "nombre": "La Liga (Spain)", "logo": ""}, {"id": 39, "nombre": "Premier (England)", "logo": ""}]
    
    lista = []
    for item in res:
        l = item["league"]
        c = item["country"]
        lista.append({"id": l["id"], "nombre": f"{l['name']} ({c['name']})", "logo": l.get("logo", "")})
    return sorted(lista, key=lambda x: x['nombre'])

@st.cache_data(ttl=3600)
def obtener_equipos_liga(league_id):
    # BUSQUEDA EN CASCADA: Intenta 2026, luego 2025, luego 2024
    for temporada in [2026, 2025, 2024]:
        data = _api_get("/teams", params={"league": league_id, "season": temporada})
        res = data.get("response", [])
        if res:
            return sorted([
                {"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
                for t in res
            ], key=lambda x: x['nombre'])
    
    # MODO RESCATE: Si ninguna temporada tiene datos, evita que la app muera
    return [{"id": 0, "nombre": "⚠️ Sin datos en API (Elija otra liga)", "logo": ""}]

def obtener_promedios_goles(team_id, league_id):
    if team_id == 0: return (1.5, 1.2) # Valores por defecto para modo rescate
    
    # Intenta obtener los últimos 10 partidos para calcular promedios reales
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": 2024, "last": 10})
    res = data.get("response", [])
    
    if res:
        goles_f = 0
        goles_c = 0
        for f in res:
            g = f.get("goals", {})
            # Detectar si el equipo era local o visitante en ese partido
            if f["teams"]["home"]["id"] == team_id:
                goles_f += (g.get("home") or 0)
                goles_c += (g.get("away") or 0)
            else:
                goles_f += (g.get("away") or 0)
                goles_c += (g.get("home") or 0)
        return (round(goles_f/len(res), 2), round(goles_c/len(res), 2))
    
    return (1.4, 1.1) # Promedio estandar si no hay historial

def obtener_h2h(id_l, id_v):
    if id_l == 0 or id_v == 0: return []
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_l}-{id_v}", "last": 5})
    res = data.get("response", [])
    h2h = []
    for f in res:
        h2h.append({
            "Fecha": f["fixture"]["date"][:10],
            "Resultado": f"{f['goals']['home']}-{f['goals']['away']}",
            "Ganador": f["teams"]["home"]["name"] if f["goals"]["home"] > f["goals"]["away"] else (f["teams"]["away"]["name"] if f["goals"]["away"] > f["goals"]["home"] else "Empate")
        })
    return h2h















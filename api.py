import requests
import streamlit as st
import time

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    """Conexión segura con manejo de errores y timeout."""
    try:
        if "general" in st.secrets and "api_key" in st.secrets["general"]:
            key = st.secrets["general"]["api_key"]
        else:
            st.error("🔑 Error: No se encontró la API KEY en los Secrets.")
            return {"response": []}
            
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        # Agregamos un timestamp para evitar datos cacheados por la red
        if params is None: params = {}
        params["_t"] = int(time.time())
        
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=12)
        
        if r.status_code != 200:
            return {"response": []}
        return r.json()
    except Exception:
        return {"response": []}

@st.cache_data(ttl=300)
def obtener_ligas():
    """Trae todas las ligas disponibles con su país."""
    data = _api_get("/leagues")
    response = data.get("response", [])
    lista = []
    for l in response:
        nombre_mostrado = f"{l['league']['name']} ({l['country']['name']})"
        lista.append({
            "id": l["league"]["id"], 
            "nombre": nombre_mostrado, 
            "logo": l["league"].get("logo", "")
        })
    return sorted(lista, key=lambda x: x['nombre']) if lista else [{"id": 140, "nombre": "La Liga (Spain)", "logo": ""}]

def obtener_temporada_actual(league_id):
    """
    En febrero de 2026, la temporada actual es la 2025 (25/26).
    Retornamos 2025 como objetivo principal.
    """
    return 2025

@st.cache_data(ttl=300)
def obtener_equipos_liga(league_id):
    """Busca equipos en 2025, si falla, busca en 2024."""
    # Intento 1: Temporada Actual 25/26
    data = _api_get("/teams", params={"league": league_id, "season": 2025})
    res = data.get("response", [])
    
    # Intento 2: Respaldo 24/25 (si la 25 está vacía en la API)
    if not res:
        data = _api_get("/teams", params={"league": league_id, "season": 2024})
        res = data.get("response", [])
        
    if not res: return []
    
    return sorted([
        {"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
        for t in res
    ], key=lambda x: x['nombre'])

def obtener_promedios_goles(team_id, league_id):
    """Calcula promedios usando la temporada más reciente con datos."""
    if not team_id: return (1.40, 1.20)
    
    # Intentamos buscar en la temporada 2025 primero
    for year in [2025, 2024]:
        data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": year, "last": 10})
        res = data.get("response", [])
        
        if res and len(res) > 2: # Si encontramos al menos 3 partidos, usamos este año
            g_f, g_c, p = 0, 0, 0
            for f in res:
                gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
                if gh is not None and ga is not None:
                    if f["teams"]["home"]["id"] == team_id:
                        g_f += gh; g_c += ga
                    else:
                        g_f += ga; g_c += gh
                    p += 1
            if p > 0:
                return (round(g_f/p, 2), round(g_c/p, 2))
                
    return (1.40, 1.20) # Valor por defecto si no hay nada en ningún año

def obtener_h2h(id_local, id_visitante):
    """Busca los últimos 5 enfrentamientos sin importar la liga o año."""
    if not id_local or not id_visitante: return []
    
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_local}-{id_visitante}", "last": 5})
    h2h_lista = []
    
    for f in data.get("response", []):
        gh, ga = f.get("goals", {}).get("home"), f.get("goals", {}).get("away")
        if gh is not None and ga is not None:
            ganador = "Empate"
            if gh > ga: ganador = f["teams"]["home"]["name"]
            elif ga > gh: ganador = f["teams"]["away"]["name"]
            
            h2h_lista.append({
                "Fecha": f["fixture"]["date"][:10], 
                "Marcador": f"{gh}-{ga}", 
                "Ganador": ganador
            })
    return h2h_lista















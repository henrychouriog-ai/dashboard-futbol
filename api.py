import requests
import streamlit as st
import datetime

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    """Función base con seguridad y manejo de errores."""
    try:
        if "general" not in st.secrets or "api_key" not in st.secrets["general"]:
            st.error("🔑 Falta la API Key en los Secrets de Streamlit.")
            return {"response": []}
            
        key = st.secrets["general"]["api_key"]
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        # Timeout de 10 segundos para evitar que la app se quede en negro
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        
        if r.status_code != 200:
            return {"response": []}
            
        return r.json()
    except Exception:
        return {"response": []}

@st.cache_data(ttl=3600)
def obtener_ligas():
    """Obtiene todas las ligas disponibles de forma ordenada."""
    data = _api_get("/leagues")
    response = data.get("response", [])
    
    if not response:
        # Fallback por si la API falla totalmente
        return [{"id": 140, "nombre": "La Liga", "logo": ""}]
    
    lista = []
    for l in response:
        if l.get("league") and l["league"].get("id"):
            lista.append({
                "id": l["league"]["id"], 
                "nombre": l["league"]["name"], 
                "logo": l["league"].get("logo", "")
            })
    return sorted(lista, key=lambda x: x['nombre'])

@st.cache_data(ttl=3600)
def obtener_temporada_actual(league_id):
    """
    Forzamos 2025 o 2024 para asegurar datos. 
    A inicios de 2026, las ligas europeas están en la temporada 2025.
    """
    return 2025

@st.cache_data(ttl=600)
def obtener_equipos_liga(league_id):
    """Busca equipos intentando primero con 2025 y luego con 2024."""
    for year in [2025, 2024]:
        data = _api_get("/teams", params={"league": league_id, "season": year})
        res = data.get("response", [])
        if res:
            return sorted([
                {"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
                for t in res
            ], key=lambda x: x['nombre'])
    return []

def obtener_promedios_goles(team_id, league_id):
    """Calcula promedios de goles basados en los últimos 10 partidos."""
    # Buscamos en la temporada actual activa
    year = obtener_temporada_actual(league_id)
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": year, "last": 10})
    res = data.get("response", [])
    
    # Si no hay datos en 2025, probamos 2024
    if len(res) < 2:
        data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": year - 1, "last": 10})
        res = data.get("response", [])

    if not res: 
        # Valores de seguridad realistas si no hay datos
        return (1.40, 1.20)

    g_f, g_c, p = 0, 0, 0
    for f in res:
        goals = f.get("goals", {})
        gh, ga = goals.get("home"), goals.get("away")
        if gh is None or ga is None: continue
        
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh
            g_c += ga
        else:
            g_f += ga
            g_c += gh
        p += 1
        
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.40, 1.20)

def obtener_h2h(id_local, id_visitante):
    """Obtiene los últimos 5 enfrentamientos directos históricos de cualquier fecha."""
    # Quitamos filtros de liga o año para que encuentre partidos SIEMPRE
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_local}-{id_visitante}", "last": 5})
    
    h2h_lista = []
    response = data.get("response", [])
    
    if not response:
        return []

    for f in response:
        goals = f.get("goals", {})
        gh, ga = goals.get("home"), goals.get("away")
        
        # Solo partidos con resultado final
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















import os
import requests
import streamlit as st

# =========================
# CONFIGURACIÓN
# =========================
def obtener_api_key():
    try:
        # Intenta sacarla de Streamlit Secrets
        return st.secrets["general"]["api_key"]
    except:
        # Si falla, busca la variable local
        return "TU_API_KEY_AQUI" 

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    key = obtener_api_key()
    headers = {"x-apisports-key": key, "Content-Type": "application/json"}
    try:
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except Exception as e:
        return {"response": []}

# =========================
# FUNCIONES SIN BLOQUEO DE CACHÉ
# =========================

@st.cache_data(ttl=3600) # Solo guarda las ligas por 1 hora
def obtener_ligas():
    data = _api_get("/leagues")
    ligas = []
    for l in data.get("response", []):
        ligas.append({
            "id": l["league"]["id"],
            "nombre": f"{l['country']['name']} - {l['league']['name']}",
            "logo": l["league"]["logo"]
        })
    return ligas

@st.cache_data(ttl=600) # Guarda los equipos por 10 minutos
def obtener_equipos_liga(league_id):
    # Intentamos temporada 2025 y si no 2024
    data = _api_get("/teams", params={"league": league_id, "season": 2025})
    if not data.get("response"):
        data = _api_get("/teams", params={"league": league_id, "season": 2024})

    equipos = []
    for t in data.get("response", []):
        equipos.append({
            "id": t["team"]["id"], 
            "nombre": t["team"]["name"],
            "logo": t["team"]["logo"]
        })
    return sorted(equipos, key=lambda x: x['nombre'])

def obtener_promedios_goles(team_id, league_id):
    # Buscamos los últimos 15 partidos para mayor precisión
    params = {"team": team_id, "league": league_id, "last": 15}
    data = _api_get("/fixtures", params=params)

    g_f, g_c, p = 0, 0, 0
    responses = data.get("response", [])
    
    if not responses:
        return (1.30, 1.10) # Valores neutros si no hay datos

    for f in responses:
        gh, ga = f["goals"]["home"], f["goals"]["away"]
        if gh is None or ga is None: continue
        
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh; g_c += ga
        else:
            g_f += ga; g_c += gh
        p += 1
    
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.30, 1.10)

def obtener_h2h(id_local, id_visitante):
    # Esta es la función que te faltaba
    h2h_query = f"{id_local}-{id_visitante}"
    data = _api_get("/fixtures/headtohead", params={"h2h": h2h_query, "last": 5})
    
    resultados = []
    for f in data.get("response", []):
        gh, ga = f["goals"]["home"], f["goals"]["away"]
        ganador = "Empate"
        if gh > ga: ganador = f["teams"]["home"]["name"]
        elif ga > gh: ganador = f["teams"]["away"]["name"]
        
        resultados.append({
            "Fecha": f["fixture"]["date"][:10],
            "Marcador": f"{gh}-{ga}",
            "Ganador": ganador
        })
    return resultados














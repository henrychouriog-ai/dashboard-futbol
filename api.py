import requests
import streamlit as st
import math

# URL base de la API
BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    """Función interna para conectar con la API usando la Key de Secrets"""
    try:
        key = st.secrets["general"]["api_key"]
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        return r.json()
    except Exception:
        return {"response": []}

@st.cache_data(ttl=3600)
def obtener_temporada_actual(league_id):
    """
    Busca automáticamente el año que la API tiene marcado como presente
    para esa liga específica. Esto hace que el código se actualice solo.
    """
    data = _api_get("/leagues", params={"id": league_id})
    for l in data.get("response", []):
        for s in l.get("seasons", []):
            if s.get("current"):
                return s.get("year")
    # Si por alguna razón no detecta la actual, usa el año del sistema
    import datetime
    return datetime.datetime.now().year

@st.cache_data(ttl=3600)
def obtener_ligas():
    """Obtiene todas las ligas disponibles"""
    data = _api_get("/leagues")
    return [{"id": l["league"]["id"], "nombre": l["league"]["name"], "logo": l["league"]["logo"]} 
            for l in data.get("response", [])]

@st.cache_data(ttl=600)
def obtener_equipos_liga(league_id):
    """Obtiene los equipos de la temporada que esté activa en este momento"""
    year = obtener_temporada_actual(league_id)
    data = _api_get("/teams", params={"league": league_id, "season": year})
    
    # Si la temporada actual aún no tiene equipos cargados, intenta con la anterior
    if not data.get("response"):
        data = _api_get("/teams", params={"league": league_id, "season": year - 1})
        
    return sorted([{"id": t["team"]["id"], "nombre": t["team"]["name"], "logo": t["team"]["logo"]} 
                   for t in data.get("response", [])], key=lambda x: x['nombre'])

def obtener_promedios_goles(team_id, league_id):
    """Calcula promedios usando la temporada presente detectada automáticamente"""
    year = obtener_temporada_actual(league_id)
    
    # Buscamos los últimos 15 partidos para tener una base estadística sólida
    data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": year, "last": 15})
    res = data.get("response", [])
    
    # Si la temporada actual tiene pocos partidos, buscamos en la anterior para no dar error
    if len(res) < 3:
        data = _api_get("/fixtures", params={"team": team_id, "league": league_id, "season": year - 1, "last": 15})
        res = data.get("response", [])

    if not res: 
        return (1.35, 1.15)  # Promedios estándar del fútbol si no hay datos

    g_f, g_c, p = 0, 0, 0
    for f in res:
        gh = f.get("goals", {}).get("home")
        ga = f.get("goals", {}).get("away")
        
        if gh is None or ga is None:
            continue
        
        if f["teams"]["home"]["id"] == team_id:
            g_f += gh
            g_c += ga
        else:
            g_f += ga
            g_c += gh
        p += 1
    
    return (round(g_f/p, 2), round(g_c/p, 2)) if p > 0 else (1.35, 1.15)

def obtener_h2h(id_local, id_visitante):
    """Obtiene los últimos enfrentamientos directos históricos"""
    data = _api_get("/fixtures/headtohead", params={"h2h": f"{id_local}-{id_visitante}", "last": 5})
    h2h_lista = []
    for f in data.get("response", []):
        gh = f.get("goals", {}).get("home")
        ga = f.get("goals", {}).get("away")
        if gh is None or ga is None:
            continue
        
        ganador = "Empate"
        if gh > ga:
            ganador = f["teams"]["home"]["name"]
        elif ga > gh:
            ganador = f["teams"]["away"]["name"]
        
        h2h_lista.append({
            "Fecha": f["fixture"]["date"][:10],
            "Marcador": f"{gh}-{ga}",
            "Ganador": ganador
        })
    return h2h_lista

# =========================
# NUEVO: Stats base de liga (placeholder seguro)
# =========================
@st.cache_data(ttl=3600)
def obtener_stats_liga(league_id):
    """
    Devuelve promedios base de la liga.
    Si la API no da stats consolidados, usamos valores estándar de fútbol.
    """
    return {
        "avg_goles_partido": 2.5,
        "avg_local": 1.4,
        "avg_visitante": 1.1
    }

# =========================
# NUEVO: Proyección Over/Under dinámica
# =========================
def proyectar_over_under(team_local_id, team_visitante_id, league_id, linea=2.5):
    """
    Proyecta Over/Under usando promedios de goles a favor/en contra de ambos equipos.
    """
    gf_local, gc_local = obtener_promedios_goles(team_local_id, league_id)
    gf_vis, gc_vis = obtener_promedios_goles(team_visitante_id, league_id)

    # Goles esperados simples (cruce de promedios)
    exp_local = (gf_local + gc_vis) / 2
    exp_vis = (gf_vis + gc_local) / 2
    total_esperado = exp_local + exp_vis

    sugerencia = "Over" if total_esperado > linea else "Under"

    return {
        "exp_local": round(exp_local, 2),
        "exp_visitante": round(exp_vis, 2),
        "total_esperado": round(total_esperado, 2),
        "linea": linea,
        "sugerencia": sugerencia
    }

# =========================
# NUEVO: Matriz de goles (Poisson simple)
# =========================
def matriz_goles(team_local_id, team_visitante_id, league_id, max_goles=5):
    """
    Genera una matriz de probabilidades de goles (0..max_goles) usando Poisson simple.
    """
    gf_local, gc_local = obtener_promedios_goles(team_local_id, league_id)
    gf_vis, gc_vis = obtener_promedios_goles(team_visitante_id, league_id)

    lambda_local = (gf_local + gc_vis) / 2
    lambda_vis = (gf_vis + gc_local) / 2

    def poisson(k, lam):
        return (math.exp(-lam) * lam**k) / math.factorial(k)

    matriz = []
    for i in range(max_goles + 1):
        fila = []
        for j in range(max_goles + 1):
            p = poisson(i, lambda_local) * poisson(j, lambda_vis)
            fila.append(round(p, 4))
        matriz.append(fila)

    return {
        "lambda_local": round(lambda_local, 2),
        "lambda_visitante": round(lambda_vis, 2),
        "matriz": matriz
    }















import requests
import streamlit as st
import time

BASE_URL = "https://v3.football.api-sports.io"

def _api_get(endpoint, params=None):
    """Realiza peticiones GET a la API con manejo robusto de errores"""
    try:
        # Intenta obtener la clave de los secrets de Streamlit
        key = st.secrets["general"]["api_key"]
        headers = {"x-apisports-key": key, "Content-Type": "application/json"}
        
        # Agregamos un timestamp para evitar cache
        if params is None: 
            params = {}
        params["v"] = int(time.time())
        
        r = requests.get(BASE_URL + endpoint, headers=headers, params=params, timeout=10)
        r.raise_for_status()  # Lanza excepción si hay error HTTP
        return r.json()
    except requests.exceptions.Timeout:
        st.warning("⏱️ Tiempo de espera agotado. Reintentando...")
        return {"response": []}
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
        return {"response": []}
    except KeyError:
        st.error("🔑 Error: No se encontró la clave API en secrets. Verifica tu configuración.")
        return {"response": []}
    except Exception as e:
        st.error(f"⚠️ Error inesperado: {e}")
        return {"response": []}

@st.cache_data(ttl=3600)
def obtener_ligas():
    """Obtiene la lista de ligas disponibles"""
    data = _api_get("/leagues")
    res = data.get("response", [])
    
    if not res:
        # Ligas de respaldo si la API falla totalmente
        st.warning("⚠️ No se pudieron cargar ligas de la API. Mostrando opciones limitadas.")
        return [
            {"id": 140, "nombre": "La Liga (Spain)", "logo": ""},
            {"id": 39, "nombre": "Premier League (England)", "logo": ""},
            {"id": 135, "nombre": "Serie A (Italy)", "logo": ""},
            {"id": 78, "nombre": "Bundesliga (Germany)", "logo": ""}
        ]
    
    lista = []
    for item in res:
        l = item.get("league", {})
        c = item.get("country", {})
        lista.append({
            "id": l.get("id"), 
            "nombre": f"{l.get('name', 'Unknown')} ({c.get('name', 'Unknown')})", 
            "logo": l.get("logo", "")
        })
    return sorted(lista, key=lambda x: x['nombre'])

@st.cache_data(ttl=3600)
def obtener_equipos_liga(league_id):
    """Obtiene equipos de una liga con búsqueda en cascada por temporadas"""
    # BÚSQUEDA EN CASCADA: Intenta 2025, luego 2024, luego 2023
    for temporada in [2025, 2024, 2023]:
        data = _api_get("/teams", params={"league": league_id, "season": temporada})
        res = data.get("response", [])
        
        if res:
            equipos = []
            for t in res:
                team_info = t.get("team", {})
                equipos.append({
                    "id": team_info.get("id", 0),
                    "nombre": team_info.get("name", "Unknown"),
                    "logo": team_info.get("logo", "")
                })
            
            if equipos:
                st.success(f"✅ Datos cargados para temporada {temporada}")
                return sorted(equipos, key=lambda x: x['nombre'])
    
    # MODO RESCATE: Si ninguna temporada tiene datos
    st.error("⚠️ No se encontraron equipos para esta liga en las temporadas recientes.")
    return [{"id": 0, "nombre": "⚠️ Sin datos disponibles (Elija otra liga)", "logo": ""}]

@st.cache_data(ttl=1800)
def obtener_promedios_goles(team_id, league_id):
    """Calcula promedios de goles a favor y en contra basados en partidos recientes"""
    if team_id == 0: 
        return (1.5, 1.2)  # Valores por defecto para modo rescate
    
    # Intenta obtener los últimos 10 partidos
    for temporada in [2025, 2024, 2023]:
        data = _api_get("/fixtures", params={
            "team": team_id, 
            "league": league_id, 
            "season": temporada, 
            "last": 10
        })
        res = data.get("response", [])
        
        if res and len(res) > 0:
            goles_favor = 0
            goles_contra = 0
            partidos_validos = 0
            
            for f in res:
                g = f.get("goals", {})
                teams = f.get("teams", {})
                home_team = teams.get("home", {})
                
                # Verificar que el partido tenga resultados válidos
                if g.get("home") is not None and g.get("away") is not None:
                    partidos_validos += 1
                    
                    # Detectar si el equipo era local o visitante
                    if home_team.get("id") == team_id:
                        goles_favor += g.get("home", 0)
                        goles_contra += g.get("away", 0)
                    else:
                        goles_favor += g.get("away", 0)
                        goles_contra += g.get("home", 0)
            
            if partidos_validos > 0:
                return (
                    round(goles_favor / partidos_validos, 2), 
                    round(goles_contra / partidos_validos, 2)
                )
    
    # Promedio estándar si no hay historial
    return (1.4, 1.1)

@st.cache_data(ttl=1800)
def obtener_h2h(id_local, id_visitante):
    """Obtiene historial de enfrentamientos directos entre dos equipos"""
    if id_local == 0 or id_visitante == 0: 
        return []
    
    data = _api_get("/fixtures/headtohead", params={
        "h2h": f"{id_local}-{id_visitante}", 
        "last": 5
    })
    res = data.get("response", [])
    
    h2h = []
    for f in res:
        fixture = f.get("fixture", {})
        goals = f.get("goals", {})
        teams = f.get("teams", {})
        
        home_team = teams.get("home", {})
        away_team = teams.get("away", {})
        home_goals = goals.get("home", 0)
        away_goals = goals.get("away", 0)
        
        # Determinar ganador
        if home_goals > away_goals:
            ganador = home_team.get("name", "Unknown")
        elif away_goals > home_goals:
            ganador = away_team.get("name", "Unknown")
        else:
            ganador = "Empate"
        
        h2h.append({
            "Fecha": fixture.get("date", "")[:10],
            "Resultado": f"{home_goals}-{away_goals}",
            "Ganador": ganador
        })
    
    return h2h















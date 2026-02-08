import streamlit as st
import math
import pandas as pd
import os

# =========================
# Configuración
# =========================
st.set_page_config(page_title="Dashboard Fútbol Pro", layout="wide")
SEASON = 2024

# =========================
# Cargar CSV locales (BLINDADO)
# =========================
@st.cache_data
def cargar_equipos():
    ruta = "data/equipos.csv"

    if not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
        st.error("❌ El archivo data/equipos.csv no existe o está vacío.")
        return pd.DataFrame(columns=["equipo", "liga", "gf", "gc", "cornersf", "cornersc", "cardsf", "cardsc", "partidos"])

    # 👇 TU CSV USA ; COMO SEPARADOR
    df = pd.read_csv(ruta, sep=";")

    # Limpieza fuerte de nombres de columnas
    df.columns = df.columns.str.strip().str.replace("\ufeff", "").str.replace("\u00a0", "")

    if "liga" not in df.columns or "equipo" not in df.columns:
        st.error(f"❌ Columnas encontradas en equipos.csv: {df.columns.tolist()}")
        st.stop()

    return df


@st.cache_data
def cargar_partidos():
    ruta = "data/partidos.csv"

    if not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
        st.warning("⚠️ data/partidos.csv está vacío. Se usará DataFrame vacío.")
        return pd.DataFrame(columns=["home", "away", "gol_home", "gol_away"])

    try:
        # 👇 Probablemente también está con ;
        df = pd.read_csv(ruta, sep=";")
        df.columns = df.columns.str.strip()
        return df
    except pd.errors.EmptyDataError:
        st.warning("⚠️ data/partidos.csv no tiene datos válidos.")
        return pd.DataFrame(columns=["home", "away", "gol_home", "gol_away"])

df_equipos = cargar_equipos()
df_partidos = cargar_partidos()

# =========================
# Reemplazo de funciones API (MISMA INTERFAZ)
# =========================
def obtener_ligas():
    ligas = []
    for liga in sorted(df_equipos["liga"].dropna().unique().tolist()):
        ligas.append({
            "id": liga,
            "nombre": liga,
            "pais": ""
        })
    return ligas

def obtener_equipos_liga(league_id, season):
    df_liga = df_equipos[df_equipos["liga"] == league_id]
    equipos = []
    for i, row in df_liga.iterrows():
        equipos.append({
            "id": row["equipo"],
            "nombre": row["equipo"]
        })
    return equipos

def obtener_partidos_con_cache(team_id, league_id, season):
    if df_partidos is None or len(df_partidos) == 0:
        return None

    required = {"home", "away", "gol_home", "gol_away"}
    if not required.issubset(set(df_partidos.columns)):
        st.warning(f"⚠️ Columnas en partidos.csv: {df_partidos.columns.tolist()}")
        return None

    df = df_partidos.copy()
    df_team = df[(df["home"] == team_id) | (df["away"] == team_id)]
    if len(df_team) == 0:
        return None
    return df_team

# =========================
# Cache de llamadas (Streamlit)
# =========================
@st.cache_data(ttl=60*60*12)
def cached_obtener_ligas():
    return obtener_ligas()

@st.cache_data(ttl=60*60*12)
def cached_obtener_equipos_liga(league_id, season):
    return obtener_equipos_liga(league_id, season)

# =========================
# Helpers UI (Cards)
# =========================
def color_por_prob(p):
    if p >= 0.7:
        return "#2ecc71"
    elif p >= 0.5:
        return "#f1c40f"
    else:
        return "#e74c3c"

def card(titulo, valor, sub="", p=None):
    bg = "#3498db" if p is None else color_por_prob(p)
    st.markdown(
        f"""
        <div style="
            background:{bg};
            padding:18px;
            border-radius:14px;
            text-align:center;
            margin-bottom:12px;
            box-shadow:0 6px 16px rgba(0,0,0,.25);
            color:white;
        ">
            <div style="font-weight:700; opacity:.95;">{titulo}</div>
            <div style="font-size:30px; font-weight:900; margin:6px 0;">{valor}</div>
            <div style="opacity:.9;">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# Poisson
# =========================
def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

def matriz(lh, la, maxg=7):
    m = {}
    for i in range(maxg + 1):
        for j in range(maxg + 1):
            m[(i, j)] = poisson_prob(lh, i) * poisson_prob(la, j)
    return m

def calcular_1x2(lh, la):
    m = matriz(lh, la)
    ph = pd_ = pa = 0
    for (i, j), p in m.items():
        if i > j:
            ph += p
        elif i == j:
            pd_ += p
        else:
            pa += p
    return ph, pd_, pa

def prob_btts(lh, la):
    m = matriz(lh, la)
    p = 0
    for (i, j), pr in m.items():
        if i > 0 and j > 0:
            p += pr
    return p

def prob_over_under_total(lmbda_total, linea):
    p_under = 0
    for k in range(0, int(math.floor(linea)) + 1):
        p_under += poisson_prob(lmbda_total, k)
    p_over = 1 - p_under
    return p_over, p_under

# =========================
# EV y Kelly
# =========================
def valor_esperado(prob, cuota):
    return prob * cuota - 1

def kelly(prob, cuota):
    b = cuota - 1
    q = 1 - prob
    if b <= 0:
        return 0
    f = (b * prob - q) / b
    return max(0, f)

# =========================
# Procesar CSV partidos
# =========================
def preparar_df(df, team_name):
    if df is None or len(df) == 0:
        return df
    df = df.copy()
    df["es_local"] = df["home"] == team_name
    df["gf"] = df.apply(lambda r: r["gol_home"] if r["es_local"] else r["gol_away"], axis=1)
    df["gc"] = df.apply(lambda r: r["gol_away"] if r["es_local"] else r["gol_home"], axis=1)
    return df

def promedios(df):
    if df is None or len(df) == 0:
        return 1.0, 1.0
    return float(df["gf"].mean()), float(df["gc"].mean())

def forma_reciente(df, n=5):
    if df is None or len(df) == 0:
        return 1.0, 1.0
    df2 = df.tail(n)
    return float(df2["gf"].mean()), float(df2["gc"].mean())

# =========================
# Sidebar
# =========================
st.sidebar.header("⚙️ Filtros")

with st.spinner("Cargando ligas..."):
    ligas_api = cached_obtener_ligas()

if not ligas_api:
    st.error("❌ No se pudieron cargar las ligas desde los CSV.")
    st.stop()

liga_sel = st.sidebar.selectbox(
    "Selecciona Liga",
    ligas_api,
    format_func=lambda x: f"{x['nombre']}"
)

if not liga_sel:
    st.warning("Selecciona una liga")
    st.stop()

LEAGUE_ID = liga_sel["id"]

with st.spinner("Cargando equipos..."):
    equipos = cached_obtener_equipos_liga(LEAGUE_ID, SEASON)

if not equipos or len(equipos) < 2:
    st.error("❌ No hay suficientes equipos para esta liga.")
    st.stop()

nombres = [e["nombre"] for e in equipos]

idx_local = 0
idx_visita = 1 if len(nombres) > 1 else 0

local_nombre = st.sidebar.selectbox("🏠 Local", nombres, index=idx_local)
visitante_nombre = st.sidebar.selectbox("✈️ Visitante", nombres, index=idx_visita)

if local_nombre == visitante_nombre:
    st.warning("⚠️ Elige equipos distintos")
    st.stop()

local = next(e for e in equipos if e["nombre"] == local_nombre)
visita = next(e for e in equipos if e["nombre"] == visitante_nombre)

st.sidebar.markdown("---")
bankroll = st.sidebar.number_input("💰 Bankroll", min_value=1.0, value=100.0, step=1.0)
kelly_factor = st.sidebar.slider("⚖️ Factor Kelly", 0.0, 1.0, 0.5, 0.05)

handicap_local = st.sidebar.selectbox("Hándicap Asiático Simple (Local)", [0, -0.5, +0.5])

# =========================
# Cargar partidos desde CSV
# =========================
with st.spinner("Cargando partidos desde CSV..."):
    df_local_raw = obtener_partidos_con_cache(local["id"], LEAGUE_ID, SEASON)
    df_visita_raw = obtener_partidos_con_cache(visita["id"], LEAGUE_ID, SEASON)

df_local = preparar_df(df_local_raw, local_nombre)
df_visita = preparar_df(df_visita_raw, visitante_nombre)

# =========================
# Promedios y forma
# =========================
lgf, lgc = promedios(df_local)
vgf, vgc = promedios(df_visita)

lgf5, lgc5 = forma_reciente(df_local, 5)
vgf5, vgc5 = forma_reciente(df_visita, 5)

lgf_mix = 0.7 * lgf + 0.3 * lgf5
lgc_mix = 0.7 * lgc + 0.3 * lgc5
vgf_mix = 0.7 * vgf + 0.3 * vgf5
vgc_mix = 0.7 * vgc + 0.3 * vgc5

lambda_local = max(0.1, (lgf_mix + vgc_mix) / 2)
lambda_visita = max(0.1, (vgf_mix + lgc_mix) / 2)
lambda_goles_total = lambda_local + lambda_visita

# =========================
# Probabilidades
# =========================
p_home, p_draw, p_away = calcular_1x2(lambda_local, lambda_visita)
p_btts = prob_btts(lambda_local, lambda_visita)

# =========================
# Tabs
# =========================
tab_partido, tab_mercados, tab_totales, tab_value, tab_datos = st.tabs(
    ["⚽ Partido", "📊 Mercados", "📈 Totales", "💰 Value & Kelly", "📄 Datos"]
)

with tab_partido:
    st.subheader(f"{local_nombre} vs {visitante_nombre}")
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Local", f"{p_home*100:.1f}%", "Probabilidad", p_home)
    with c2:
        card("Empate", f"{p_draw*100:.1f}%", "Probabilidad", p_draw)
    with c3:
        card("Visitante", f"{p_away*100:.1f}%", "Probabilidad", p_away)

with tab_mercados:
    st.subheader("BTTS")
    card("BTTS Sí", f"{p_btts*100:.1f}%", "Ambos marcan", p_btts)
    card("BTTS No", f"{(1-p_btts)*100:.1f}%", "No ambos marcan", 1-p_btts)

with tab_totales:
    st.subheader("Totales de Goles (λ)")
    card("Lambda Local", f"{lambda_local:.2f}")
    card("Lambda Visitante", f"{lambda_visita:.2f}")
    card("Lambda Total", f"{lambda_goles_total:.2f}")

with tab_value:
    st.info("Aquí luego metemos el cálculo de Value y Kelly con tus cuotas.")

with tab_datos:
    st.subheader("Debug CSV")
    st.write("DF Local:")
    st.write(df_local.head() if df_local is not None else "Vacío")
    st.write("DF Visitante:")
    st.write(df_visita.head() if df_visita is not None else "Vacío")
    st.write("Columnas equipos:", df_equipos.columns.tolist())
    st.write("Columnas partidos:", df_partidos.columns.tolist())

st.info("💡 Usando solo datos locales desde CSV. No se consume API.")







































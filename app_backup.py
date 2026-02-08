import streamlit as st
import pandas as pd
import math

import streamlit as st

# Estado del tema
if "tema" not in st.session_state:
    st.session_state.tema = "dark"

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuración")
    modo = st.toggle("🌗 Modo oscuro", value=(st.session_state.tema == "dark"))

    if modo:
        st.session_state.tema = "dark"
    else:
        st.session_state.tema = "light"
def aplicar_tema(tema):
    if tema == "dark":
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(180deg, #020617 0%, #020617 100%);
            color: #e5e7eb;
        }

        h1, h2, h3 {
            color: #e5e7eb;
        }

        /* Cards */
        .card {
            background: linear-gradient(145deg, #020617, #020617);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        }

        /* Métricas */
        div[data-testid="stMetric"] {
            background-color: #020617;
            border-radius: 14px;
            padding: 15px;
            box-shadow: 0 0 12px rgba(0,0,0,0.5);
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
            color: #020617;
        }

        h1, h2, h3 {
            color: #020617;
        }

        /* Cards */
        .card {
            background: #ffffff;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        }

        /* Métricas */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-radius: 14px;
            padding: 15px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)


aplicar_tema(st.session_state.tema)


def card(titulo, valor, subtitulo="", emoji=""):
    st.markdown(f"""
    <div class="card">
        <h3>{emoji} {titulo}</h3>
        <h2 style="margin-top:10px;">{valor}</h2>
        <p style="opacity:0.8;">{subtitulo}</p>
    </div>
    """, unsafe_allow_html=True)



# -------------------------
# Configuración de la página
# -------------------------
st.set_page_config(page_title="Dashboard Fútbol", layout="wide")
st.markdown("""
<style>
body {
    background-color: #0f172a;
}
section[data-testid="stSidebar"] {
    background-color: #020617;
}
h1, h2, h3, h4 {
    color: #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

st.title("⚽ Dashboard de Análisis de Fútbol")
st.caption("Modelo estadístico Poisson • Goles, Corners y Tarjetas • Enfoque en valor de apuesta")
st.divider()

# -------------------------
# Utilidades
# -------------------------
def formato_prob(p):
    pct = round(p * 100, 1)
    if pct >= 60:
        return f"🟢 {pct}%"
    elif pct >= 50:
        return f"🟡 {pct}%"
    else:
        return f"🔴 {pct}%"

todas_las_probs = {}

# -------------------------
# Cargar datos
# -------------------------
df = pd.read_csv("data/equipos.csv", sep=";")
df.columns = df.columns.str.replace(",", "", regex=False).str.strip().str.lower()

# -------------------------
# Barra lateral (filtros)
# -------------------------
st.sidebar.header("⚙️ Filtros")

ligas = sorted(df["liga"].unique())
liga = st.sidebar.selectbox("Selecciona Liga", ligas)

df_liga = df[df["liga"] == liga]
equipos = df_liga["equipo"].tolist()

local = st.sidebar.selectbox("Equipo Local", equipos)
visitante = st.sidebar.selectbox("Equipo Visitante", equipos)

# -------------------------
# Inputs de apuesta
# -------------------------
st.sidebar.subheader("💵 Parámetros de apuesta")

cuota_usuario = st.sidebar.number_input(
    "Cuota de la casa",
    min_value=1.01,
    max_value=100.0,
    value=2.00,
    step=0.01
)

bankroll = st.sidebar.number_input(
    "Bankroll",
    min_value=1.0,
    value=100.0,
    step=1.0
)

kelly_factor = st.sidebar.slider(
    "Factor Kelly (riesgo)",
    min_value=0.1,
    max_value=1.0,
    value=0.5,
    step=0.1
)

# -------------------------
# Funciones de datos
# -------------------------
def datos_equipo(nombre):
    fila = df[df["equipo"] == nombre].iloc[0]
    gf = fila["gf"]
    gc = fila["gc"]
    pj = fila["partidos"]
    return gf / pj, gc / pj

def datos_equipo_corners(nombre):
    fila = df[df["equipo"] == nombre].iloc[0]
    cf = fila["cornersf"]
    cc = fila["cornersc"]
    pj = fila["partidos"]
    return cf / pj, cc / pj

def datos_equipo_tarjetas(nombre):
    fila = df[df["equipo"] == nombre].iloc[0]
    tf = fila["cardsf"]
    tc = fila["cardsc"]
    pj = fila["partidos"]
    return tf / pj, tc / pj

# -------------------------
# Datos equipos
# -------------------------
local_gf, local_gc = datos_equipo(local)
vis_gf, vis_gc = datos_equipo(visitante)

lambda_local = (local_gf + vis_gc) / 2
lambda_visita = (vis_gf + local_gc) / 2
lambda_total = lambda_local + lambda_visita

local_cf, local_cc = datos_equipo_corners(local)
vis_cf, vis_cc = datos_equipo_corners(visitante)

lambda_corners_local = (local_cf + vis_cc) / 2
lambda_corners_vis = (vis_cf + local_cc) / 2
lambda_corners_total = lambda_corners_local + lambda_corners_vis

local_tf, local_tc = datos_equipo_tarjetas(local)
vis_tf, vis_tc = datos_equipo_tarjetas(visitante)

lambda_cards_local = (local_tf + vis_tc) / 2
lambda_cards_vis = (vis_tf + local_tc) / 2
lambda_cards_total = lambda_cards_local + lambda_cards_vis

# -------------------------
# Poisson
# -------------------------
def poisson_prob(lmbda, k):
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

def matriz_resultados(lambda_home, lambda_away, max_goals=5):
    matriz = {}
    for i in range(0, max_goals + 1):
        for j in range(0, max_goals + 1):
            p = poisson_prob(lambda_home, i) * poisson_prob(lambda_away, j)
            matriz[(i, j)] = p
    return matriz

def calcular_1x2_y_btts(lambda_home, lambda_away):
    matriz = matriz_resultados(lambda_home, lambda_away, 5)

    p_home = p_draw = p_away = p_btts = 0

    for (i, j), p in matriz.items():
        if i > j:
            p_home += p
        elif i == j:
            p_draw += p
        else:
            p_away += p

        if i > 0 and j > 0:
            p_btts += p

    return p_home, p_draw, p_away, p_btts

def prob_over(linea, lmbda):
    limite = int(linea)
    p = 0
    for i in range(0, limite + 1):
        p += poisson_prob(lmbda, i)
    return 1 - p

# -------------------------
# Probabilidades principales
# -------------------------
p_home, p_draw, p_away, p_btts = calcular_1x2_y_btts(lambda_local, lambda_visita)

# Asian simple
p_local_m05 = p_home
p_visitante_p05 = p_away + p_draw
p_local_p05 = p_home + p_draw
p_visitante_m05 = p_away

# -------------------------
# Tabs
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "⚽ Partido",
    "📊 Mercados",
    "🤖 Recomendación",
    "🚩 Corners & 🟨 Tarjetas"
])

# =========================
# TAB 1
# =========================
with tab1:
    st.title("⚽ Partido")
    st.caption("Resumen estadístico del encuentro")
    st.divider()


    c1, c2, c3, c4 = st.columns(4)

    with c1:
        card("Liga", liga, emoji="🏆")

    with c2:
        card(f"{local}", f"λ {round(lambda_local,2)}", "Goles esperados", "🏠")

    with c3:
        card(f"{visitante}", f"λ {round(lambda_visita,2)}", "Goles esperados", "✈️")

    with c4:
        card("Total", f"λ {round(lambda_total,2)}", "Goles totales", "⚽")


# =========================
# TAB 2
# =========================
# =========================
# TAB 2
# =========================
with tab2:
    st.markdown("## 📈 Mercados del Partido")
    st.caption("Probabilidades calculadas con modelo Poisson")


    # =========================
    # 1X2
    # =========================
    st.subheader("🔮 1X2 (Resultado Final)")

    picks_1x2 = {
        f"{local} gana": p_home,
        "Empate": p_draw,
        f"{visitante} gana": p_away
    }

    cols = st.columns(3)

    for i, (pick, prob) in enumerate(picks_1x2.items()):
        todas_las_probs[pick] = prob
        emoji = "🟢" if prob >= 0.6 else "🟡" if prob >= 0.5 else "🔴"

        with cols[i]:
            card(pick, f"{round(prob*100,1)}%", "Probabilidad modelo", emoji)

    st.divider()

    # =========================
    # DOBLE OPORTUNIDAD
    # =========================
    st.subheader("🔁 Doble Oportunidad")

    p_1x = p_home + p_draw
    p_x2 = p_draw + p_away
    p_12 = p_home + p_away

    picks_do = {
        "1X (Local o Empate)": p_1x,
        "X2 (Empate o Visitante)": p_x2,
        "12 (Cualquiera gana)": p_12
    }

    cols = st.columns(3)

    for i, (pick, prob) in enumerate(picks_do.items()):
        todas_las_probs[pick] = prob
        emoji = "🟢" if prob >= 0.6 else "🟡" if prob >= 0.5 else "🔴"

        with cols[i]:
            card(pick, f"{round(prob*100,1)}%", "Probabilidad modelo", emoji)

    st.divider()

    # =========================
    # HANDICAP ASIÁTICO SIMPLE
    # =========================
    st.markdown("### 📐 Handicap Asiático Simple")

h1, h2 = st.columns(2)

with h1:
    card(f"{local} -0.5", formato_prob(p_local_m05), "Probabilidad modelo", "🏠")
    card(f"{local} +0.5", formato_prob(p_local_p05), "Probabilidad modelo", "🏠")

    todas_las_probs[f"{local} -0.5"] = p_local_m05
    todas_las_probs[f"{local} +0.5"] = p_local_p05

with h2:
    card(f"{visitante} -0.5", formato_prob(p_visitante_m05), "Probabilidad modelo", "✈️")
    card(f"{visitante} +0.5", formato_prob(p_visitante_p05), "Probabilidad modelo", "✈️")

    todas_las_probs[f"{visitante} -0.5"] = p_visitante_m05
    todas_las_probs[f"{visitante} +0.5"] = p_visitante_p05



# =========================
# TAB 3
# =========================
with tab3:
    st.title("🤖 Recomendación del Sistema")
    st.caption("Selección automática basada en valor estadístico")
    st.divider()

    picks_filtrados = {k: v for k, v in todas_las_probs.items() if 0.55 <= v <= 0.80}

    if picks_filtrados:
        mejor_pick = max(picks_filtrados, key=picks_filtrados.get)
        p_modelo = picks_filtrados[mejor_pick]
        ev = (p_modelo * cuota_usuario) - 1

        # ===== CARD PRINCIPAL =====
        card(
            "🔥 Pick recomendado",
            mejor_pick,
            f"Probabilidad del modelo: {round(p_modelo*100,1)}%",
            "🤖"
        )

        st.subheader("📐 Análisis de Valor")
        st.write(f"📊 Probabilidad del modelo: **{round(p_modelo*100,2)}%**")
        st.write(f"💵 Cuota ingresada: **{cuota_usuario}**")
        st.write(f"📈 EV = (p × cuota) - 1 = **{round(ev,3)}**")

        if ev > 0:
            f_kelly = (p_modelo * cuota_usuario - 1) / (cuota_usuario - 1)
            f_real = f_kelly * kelly_factor
            stake = bankroll * f_real

            st.subheader("📏 Stake recomendado (Kelly)")
            st.write(f"⚖️ Kelly aplicado: **{round(f_real*100,2)}%** del bankroll")
            st.write(f"💵 Stake sugerido: **{round(stake,2)}**")

            if stake <= 0:
                st.warning("El stake calculado es 0 o negativo. No conviene apostar.")
        else:
            st.error("❌ Sin valor estadístico (EV negativo)")

    else:
        st.warning("⚠️ No hay picks en rango de valor (55% - 80%).")


# =========================
# TAB 4
# =========================
with tab4:
    st.title("🚩 Corners & 🟨 Tarjetas")
    st.caption("Mercados secundarios con modelo Poisson")
    st.divider()


    # =========================
    # 🚩 CORNERS
    # =========================
    st.subheader("🚩 Corners Totales")

    p_corners_over_9 = prob_over(9.5, lambda_corners_total)

    colC1, colC2 = st.columns(2)

    with colC1:
        card(
            "λ Corners Totales",
            f"{round(lambda_corners_total, 2)}",
            "Media esperada del partido",
            "🚩"
        )

    emoji_corners = "🟢" if p_corners_over_9 >= 0.6 else "🟡" if p_corners_over_9 >= 0.5 else "🔴"

    with colC2:
        card(
            "Over 9.5 Corners",
            f"{round(p_corners_over_9*100,1)}%",
            "Probabilidad del modelo",
            emoji_corners
        )

    todas_las_probs["Corners Over 9.5"] = p_corners_over_9

    st.divider()

    # =========================
    # 🟨 TARJETAS
    # =========================
    st.subheader("🟨 Tarjetas Totales")

    st.metric("📊 λ Tarjetas Totales", f"{round(lambda_cards_total, 2)}")

    lineas_cards = [2.5, 3.5, 4.5, 5.5, 6.5]
    cols_cards = st.columns(len(lineas_cards))

    for i, l in enumerate(lineas_cards):
        p = prob_over(l, lambda_cards_total)
        todas_las_probs[f"Tarjetas Over {l}"] = p

        emoji = "🟢" if p >= 0.6 else "🟡" if p >= 0.5 else "🔴"

        with cols_cards[i]:
            card(
                f"Over {l} Tarjetas",
                f"{round(p*100,1)}%",
                "Probabilidad del modelo",
                emoji
            )



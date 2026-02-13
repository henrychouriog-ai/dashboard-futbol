import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import api  
import math

# ==========================================
# 🎨 CONFIGURACIÓN Y ESTILO v6.2 (MEJORADO)
# ==========================================
st.set_page_config(
    page_title="BETPLAY AI ANALYZER PRO", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #050a14; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    
    .stTabs [data-baseweb="tab"] { 
        background-color: #0e1629; color: #94a3b8; border-radius: 8px 8px 0 0;
        padding: 10px 20px; border: 1px solid #1e293b;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #009345 !important; color: white !important; 
    }

    .mkt-card {
        background: #0e1629; padding: 20px; border-radius: 15px;
        border: 1px solid #1e293b; text-align: center;
    }

    .match-banner {
        background: linear-gradient(135deg, #004a99 0%, #050a14 100%);
        padding: 35px; border-radius: 25px; text-align: center; 
        border: 1px solid #1e3a8a; border-bottom: 6px solid #009345;
        margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .betplay-header {
        background-color: #004a99; color: white; padding: 12px; 
        border-radius: 8px; font-weight: bold; margin: 20px 0;
        border-left: 6px solid #009345; display: flex; 
        justify-content: space-between; align-items: center;
    }
    
    .stButton>button {
        width: 100%; background-color: #009345; color: white;
        border-radius: 10px; border: none; font-weight: bold;
        padding: 10px;
    }
    
    /* Mejoras para móvil */
    @media (max-width: 768px) {
        .match-banner { padding: 20px; }
        .mkt-card { padding: 15px; }
        .betplay-header { font-size: 0.9rem; padding: 10px; }
    }
    </style>
""", unsafe_allow_html=True)

# --- Funciones Core ---
def poisson_prob(lmbda, k):
    """Calcula probabilidad de Poisson para k eventos con tasa lambda"""
    if lmbda <= 0: 
        return 1.0 if k == 0 else 0.0
    try:
        return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)
    except (OverflowError, ValueError):
        return 0.0

def calcular_o_u(lmbda, limite):
    """Calcula probabilidades Over/Under para una línea específica"""
    try:
        prob_under = sum(poisson_prob(lmbda, k) for k in range(int(limite) + 1))
        prob_over = 1 - prob_under
        return prob_over * 100, prob_under * 100
    except Exception:
        return (50.0, 50.0)  # Valores neutros en caso de error

# ==========================================
# 🛠️ SIDEBAR (ESTILO v6.2)
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: #0e1629; 
                    border-radius: 15px; border: 1px solid #1e3a8a; margin-bottom: 10px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/0/06/Flag_of_Venezuela.svg" 
                 width="90" style="border-radius: 5px; margin-bottom: 10px;">
            <p style="color: #009345; font-size: 0.8rem; font-weight: bold; 
                      margin:0; letter-spacing: 2px;">ANALYTICS PRO</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 ACTUALIZAR DATOS API"):
        st.cache_data.clear()
        st.success("✅ Cache limpiado")
        st.rerun()

    # Obtener ligas
    try:
        ligas = api.obtener_ligas()
    except Exception as e:
        st.error(f"Error al cargar ligas: {e}")
        st.stop()

    if not ligas:
        st.error("⚠️ No se pudieron cargar las ligas. Verifica tu conexión y API key.")
        st.stop()
    
    # Selección de liga
    liga_sel = st.selectbox(
        "Seleccionar Liga", 
        ligas, 
        format_func=lambda x: x['nombre']
    )
    
    if liga_sel.get("logo"):
        st.markdown(
            f'<div style="text-align: center; margin-bottom:15px;">'
            f'<img src="{liga_sel["logo"]}" width="45"></div>', 
            unsafe_allow_html=True
        )

    # Obtener equipos
    try:
        equipos = api.obtener_equipos_liga(liga_sel['id'])
    except Exception as e:
        st.error(f"Error al cargar equipos: {e}")
        st.stop()

    if not equipos or equipos[0]['id'] == 0:
        st.error("⚠️ No hay equipos disponibles para esta liga. Intenta con otra.")
        st.stop()

    # Selección de equipos
    local_obj = st.selectbox(
        "🏠 Local", 
        equipos, 
        index=0, 
        format_func=lambda x: x['nombre']
    )
    
    visit_obj = st.selectbox(
        "✈️ Visitante", 
        equipos, 
        index=1 if len(equipos) > 1 else 0, 
        format_func=lambda x: x['nombre']
    )
    
    # Validación de selección duplicada
    if local_obj['id'] == visit_obj['id'] and local_obj['id'] != 0:
        st.warning("⚠️ Has seleccionado el mismo equipo dos veces. Por favor elige equipos diferentes.")
    
    # Obtención de datos reales
    try:
        xh_f, xh_c = api.obtener_promedios_goles(local_obj['id'], liga_sel['id'])
        xa_f, xa_c = api.obtener_promedios_goles(visit_obj['id'], liga_sel['id'])
    except Exception as e:
        st.warning(f"⚠️ Error al obtener promedios: {e}. Usando valores por defecto.")
        xh_f, xh_c = 1.4, 1.1
        xa_f, xa_c = 1.2, 1.3
    
    # Cálculo de Lambdas (Expectativa de goles)
    l_h = (xh_f + xa_c) / 2
    l_a = (xa_f + xh_c) / 2
    
    st.markdown("---")
    st.markdown("### ⚙️ Ajustes Adicionales")
    l_corners = st.slider("Expectativa Córners", 5.0, 15.0, 9.5, 0.5)
    l_tarjetas = st.slider("Expectativa Tarjetas", 0.0, 10.0, 4.2, 0.1)

# --- VALIDACIÓN FINAL ---
if local_obj['id'] == visit_obj['id'] and local_obj['id'] != 0:
    st.error("⚠️ Por favor selecciona equipos diferentes para continuar.")
    st.stop()

# --- PROCESAMIENTO MATEMÁTICO ---
ph, pe, pa = 0.0, 0.0, 0.0

try:
    for i in range(10):
        for j in range(10):
            p = poisson_prob(l_h, i) * poisson_prob(l_a, j)
            if i > j: 
                ph += p
            elif i == j: 
                pe += p
            else: 
                pa += p

    total_p = ph + pe + pa
    if total_p > 0:
        ph, pe, pa = ph/total_p, pe/total_p, pa/total_p
    else:
        ph, pe, pa = 0.33, 0.33, 0.34
except Exception as e:
    st.warning(f"Error en cálculo de probabilidades: {e}")
    ph, pe, pa = 0.33, 0.33, 0.34

# BTTS (Ambos equipos marcan)
try:
    prob_btts_si = (1 - poisson_prob(l_h, 0)) * (1 - poisson_prob(l_a, 0))
    prob_btts_no = 1 - prob_btts_si
    btts_label = "BTTS: SÍ" if prob_btts_si >= 0.5 else "BTTS: NO"
    btts_perc = prob_btts_si if prob_btts_si >= 0.5 else prob_btts_no
    btts_color = "#009345" if prob_btts_si >= 0.5 else "#dc2626"
except Exception:
    prob_btts_si = 0.5
    prob_btts_no = 0.5
    btts_label = "BTTS: SÍ"
    btts_perc = 0.5
    btts_color = "#009345"

# Matriz de resultados exactos
matriz_vals = np.zeros((6, 6))
try:
    for i in range(6):
        for j in range(6):
            matriz_vals[i, j] = poisson_prob(l_h, i) * poisson_prob(l_a, j) * 100
except Exception:
    pass

# ==========================================
# 🏟️ DASHBOARD PRINCIPAL
# ==========================================
st.markdown(f"""
    <div class="match-banner">
        <div style="display: flex; justify-content: space-around; align-items: center; 
                    flex-wrap: wrap;">
            <div style="text-align: center; width: 30%; min-width: 150px;">
                <img src="{local_obj.get('logo','')}" width="95" style="max-width: 100%;">
                <p style="color: white; font-weight: bold; margin-top: 10px; font-size: 0.9rem;">
                    {local_obj['nombre']}
                </p>
            </div>
            <div style="width: 30%; text-align: center; min-width: 150px;">
                <img src="{liga_sel.get('logo', '')}" width="50" style="max-width: 100%;">
                <h1 style='color:white; margin:10px 0;'>VS</h1>
                <p style='color:#009345; font-weight:bold; font-size: 0.8rem;'>
                    {liga_sel['nombre']}
                </p>
            </div>
            <div style="text-align: center; width: 30%; min-width: 150px;">
                <img src="{visit_obj.get('logo','')}" width="95" style="max-width: 100%;">
                <p style="color: white; font-weight: bold; margin-top: 10px; font-size: 0.9rem;">
                    {visit_obj['nombre']}
                </p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Tabs principales
t1, t2, t3, t4 = st.tabs(["📈 PROYECCIONES", "🎯 LÍNEAS O/U", "📊 MATRIZ", "💰 COMPARADOR"])

with t1:
    st.markdown('<div class="betplay-header">Probabilidades Principales</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1: 
        st.markdown(
            f'<div class="mkt-card"><small>{local_obj["nombre"].upper()}</small>'
            f'<h2 style="color:#009345;">{ph*100:.1f}%</h2></div>', 
            unsafe_allow_html=True
        )
    with c2: 
        st.markdown(
            f'<div class="mkt-card"><small>EMPATE</small>'
            f'<h2 style="color:#009345;">{pe*100:.1f}%</h2></div>', 
            unsafe_allow_html=True
        )
    with c3: 
        st.markdown(
            f'<div class="mkt-card"><small>{visit_obj["nombre"].upper()}</small>'
            f'<h2 style="color:#009345;">{pa*100:.1f}%</h2></div>', 
            unsafe_allow_html=True
        )
    with c4: 
        st.markdown(
            f'<div class="mkt-card"><small>{btts_label}</small>'
            f'<h2 style="color:{btts_color};">{btts_perc*100:.1f}%</h2></div>', 
            unsafe_allow_html=True
        )

    st.markdown('<div class="betplay-header">⚔️ ÚLTIMOS ENFRENTAMIENTOS DIRECTOS (H2H)</div>', 
                unsafe_allow_html=True)
    
    try:
        h2h_data = api.obtener_h2h(local_obj['id'], visit_obj['id'])
        if h2h_data:
            st.table(pd.DataFrame(h2h_data)) 
        else:
            st.info("ℹ️ No se encontraron enfrentamientos directos recientes.")
    except Exception as e:
        st.warning(f"⚠️ No se pudieron cargar los enfrentamientos: {e}")

with t2:
    st.markdown('<div class="betplay-header">⚽ GOLES TOTALES</div>', unsafe_allow_html=True)
    g_lines = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    cols_g = st.columns(6)
    
    for i, l in enumerate(g_lines):
        p_o, p_u = calcular_o_u(l_h + l_a, l)
        cols_g[i].markdown(
            f'<div class="mkt-card"><small>{l}</small><br>'
            f'<b>O: {p_o:.1f}%</b><br>'
            f'<small style="color:#94a3b8">U: {p_u:.1f}%</small></div>', 
            unsafe_allow_html=True
        )

    st.markdown('<div class="betplay-header">🚩 CÓRNERS Y TARJETAS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        p_o, p_u = calcular_o_u(l_corners, 9.5)
        st.markdown(
            f'<div class="mkt-card">CÓRNERS (9.5)<br>'
            f'<b>O: {p_o:.1f}%</b><br>'
            f'<small style="color:#94a3b8">U: {p_u:.1f}%</small></div>', 
            unsafe_allow_html=True
        )
    with c2:
        p_o, p_u = calcular_o_u(l_tarjetas, 4.5)
        st.markdown(
            f'<div class="mkt-card">TARJETAS (4.5)<br>'
            f'<b>O: {p_o:.1f}%</b><br>'
            f'<small style="color:#94a3b8">U: {p_u:.1f}%</small></div>', 
            unsafe_allow_html=True
        )

with t3:
    st.markdown('<div class="betplay-header">📍 MATRIZ DE MARCADORES EXACTOS</div>', 
                unsafe_allow_html=True)
    
    try:
        fig = px.imshow(
            matriz_vals, 
            text_auto=".1f", 
            color_continuous_scale='Greens', 
            x=['0','1','2','3','4','5'], 
            y=['0','1','2','3','4','5'],
            labels=dict(x="Goles Visitante", y="Goles Local", color="Probabilidad %")
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            font_color="white", 
            plot_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=0,r=0,t=30,b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error al generar matriz: {e}")

with t4:
    st.markdown('<div class="betplay-header">💰 COMPARADOR DE VALOR Y STAKE DINÁMICO</div>', 
                unsafe_allow_html=True)
    
    with st.expander("📝 CONFIGURAR CUOTAS BETPLAY", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        cuo_l = c1.number_input(f"Cuota {local_obj['nombre']}", 1.0, 20.0, 2.0, step=0.01)
        cuo_e = c2.number_input("Cuota Empate", 1.0, 20.0, 3.2, step=0.01)
        cuo_v = c3.number_input(f"Cuota {visit_obj['nombre']}", 1.0, 20.0, 3.5, step=0.01)
        
        c1, c2, c3 = st.columns(3)
        cuo_bs = c1.number_input("BTTS SÍ", 1.0, 10.0, 1.8, step=0.01)
        cuo_bn = c2.number_input("BTTS NO", 1.0, 10.0, 1.9, step=0.01)
        bank = c3.number_input("Bankroll Actual ($)", value=100000, step=1000)

    # Análisis de valor
    comparativa = [
        {"Mercado": "1 (Local)", "Prob": ph, "Cuota": cuo_l},
        {"Mercado": "X (Empate)", "Prob": pe, "Cuota": cuo_e},
        {"Mercado": "2 (Visita)", "Prob": pa, "Cuota": cuo_v},
        {"Mercado": "BTTS SÍ", "Prob": prob_btts_si, "Cuota": cuo_bs},
        {"Mercado": "BTTS NO", "Prob": prob_btts_no, "Cuota": cuo_bn},
    ]
    
    df_b = pd.DataFrame(comparativa)
    df_b["Edge %"] = ((df_b["Prob"] * df_b["Cuota"]) - 1) * 100
    
    # Cálculo de Stake Dinámico basado en Edge y Probabilidad (Kelly simplificado)
    def calcular_monto(row):
        if row["Edge %"] > 0:
            # Kelly simplificado con factor de seguridad 0.1 (10% del bankroll máximo)
            stake = (row["Edge %"] / 100) * (bank * 0.1) 
            return max(0, int(stake))  # Asegurar que no sea negativo
        return 0

    df_b["Stake $"] = df_b.apply(calcular_monto, axis=1)
    df_b["Stake Sugerido"] = df_b["Stake $"].apply(lambda x: f"${x:,}")
    
    # Formateo de tabla
    st.dataframe(
        df_b[["Mercado", "Prob", "Cuota", "Edge %", "Stake Sugerido"]].style.format({
            "Prob": "{:.1%}", 
            "Cuota": "{:.2f}", 
            "Edge %": "{:.1f}%"
        }),
        use_container_width=True
    )
    
    # Recomendación
    mejor_apuesta = df_b.loc[df_b["Edge %"].idxmax()]
    if mejor_apuesta["Edge %"] > 0:
        st.success(
            f"💡 **Mejor Valor**: {mejor_apuesta['Mercado']} "
            f"(Edge: {mejor_apuesta['Edge %']:.1f}%) - "
            f"Stake sugerido: {mejor_apuesta['Stake Sugerido']}"
        )
    else:
        st.warning("⚠️ No se detectaron apuestas con valor positivo.")

st.caption("v6.2 - Motor Estabilizado | Búsqueda Multi-Temporada | Manejo Robusto de Errores")







































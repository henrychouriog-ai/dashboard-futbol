import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import api  
import math

# ==========================================
# 🎨 CONFIGURACIÓN Y ESTILO v6.7 (MÓVIL PRO)
# ==========================================
st.set_page_config(page_title="BETPLAY AI ANALYZER", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #050a14; }
    .stTabs [data-baseweb="tab"] { font-size: 12px; padding: 10px; }
    .mkt-card { 
        background: #0e1629; padding: 15px; border-radius: 12px; 
        border: 1px solid #1e293b; text-align: center; margin-bottom: 10px;
    }
    .betplay-header {
        background-color: #004a99; color: white; padding: 10px; 
        border-radius: 8px; border-left: 5px solid #009345; margin: 15px 0;
    }
    .match-banner {
        background: linear-gradient(135deg, #004a99 0%, #050a14 100%);
        padding: 20px; border-radius: 20px; text-align: center; border-bottom: 5px solid #009345;
    }
    </style>
""", unsafe_allow_html=True)

def poisson_prob(lmbda, k):
    if lmbda <= 0: return 1.0 if k == 0 else 0.0
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

# ==========================================
# 🛠️ SIDEBAR - CONTROL DE EQUIPOS
# ==========================================
with st.sidebar:
    st.title("⚽ BETPLAY AI")
    if st.button("🔄 REFRESCAR TODO"):
        api.limpiar_cache_completo()
        st.rerun()

    ligas = api.obtener_ligas()
    if ligas:
        liga_sel = st.selectbox("Liga", ligas, format_func=lambda x: x['nombre'])
        equipos = api.obtener_equipos_liga(liga_sel['id'])
        
        # Keys únicas para forzar el cambio de datos
        local_obj = st.selectbox("🏠 Local", equipos, index=0, key="L1")
        visit_obj = st.selectbox("✈️ Visita", equipos, index=1 if len(equipos)>1 else 0, key="V1")
        
        # OBTENCIÓN DE DATOS DINÁMICOS
        xhf, xhc = api.obtener_promedios_goles(local_obj['id'], liga_sel['id'])
        xaf, xac = api.obtener_promedios_goles(visit_obj['id'], liga_sel['id'])
        
        # Lambdas calculadas al momento
        lh, la = (xhf + xac)/2, (xaf + xhc)/2
        
        st.divider()
        l_corners = st.slider("Expectativa Córners", 5.0, 15.0, 9.5)
        l_cards = st.slider("Expectativa Tarjetas", 0.0, 10.0, 4.5)
    else:
        st.stop()

# ==========================================
# 📊 CÁLCULOS EN TIEMPO REAL
# ==========================================
ph, pe, pa = 0, 0, 0
matriz_vals = np.zeros((6, 6))
for i in range(6):
    for j in range(6):
        prob = poisson_prob(lh, i) * poisson_prob(la, j)
        matriz_vals[i, j] = prob * 100
        if i > j: ph += prob
        elif i == j: pe += prob
        else: pa += prob

# ==========================================
# 🏟️ DASHBOARD MÓVIL
# ==========================================
st.markdown(f"""
    <div class="match-banner">
        <h3 style="color:white; margin:0;">{local_obj['nombre']} vs {visit_obj['nombre']}</h3>
        <p style="color:#009345; font-size:12px;">{liga_sel['solo_nombre']}</p>
    </div>
""", unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["📊 ANALISIS", "🎯 LINEAS", "🏁 MATRIZ", "💰 VALUE"])

with t1:
    st.markdown('<div class="betplay-header">Probabilidades 1X2</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="mkt-card"><small>1</small><br><b style="color:#009345;">{ph*100:.1f}%</b></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="mkt-card"><small>X</small><br><b style="color:#009345;">{pe*100:.1f}%</b></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="mkt-card"><small>2</small><br><b style="color:#009345;">{pa*100:.1f}%</b></div>', unsafe_allow_html=True)

    st.markdown('<div class="betplay-header">⚔️ ENFRENTAMIENTOS H2H</div>', unsafe_allow_html=True)
    h2h_list = api.obtener_h2h(local_obj['id'], visit_obj['id'])
    if h2h_list:
        for m in h2h_list:
            st.markdown(f"**{m['fecha']}**: {m['marcador']} → *Ganador: {m['ganador']}*")
    else:
        st.write("No hay enfrentamientos recientes registrados.")

with t2:
    st.markdown('<div class="betplay-header">⚽ GOLES TOTALES</div>', unsafe_allow_html=True)
    for line in [1.5, 2.5, 3.5]:
        p_under = sum(poisson_prob(lh+la, k) for k in range(int(line) + 1))
        st.write(f"**Línea {line}:** Over {(1-p_under)*100:.1f}% | Under {p_under*100:.1f}%")

with t3:
    fig = px.imshow(matriz_vals, text_auto=".1f", color_continuous_scale='Greens',
                    x=['0','1','2','3','4','5'], y=['0','1','2','3','4','5'],
                    labels=dict(x="Visita", y="Local", color="%"))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True)

with t4:
    st.info("Ingresa la cuota de tu casa de apuestas para ver si hay valor (Edge).")
    cuota_casa = st.number_input("Cuota Local", 1.1, 10.0, 2.0)
    edge = (ph * cuota_casa) - 1
    if edge > 0:
        st.success(f"¡VALOR DETECTADO! Edge: {edge*100:.2f}%")
    else:
        st.error(f"Sin valor. Edge: {edge*100:.2f}%")

st.caption("v6.7 Pro - Optimizado para Chrome Mobile")







































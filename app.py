import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import api  
import math

# ==========================================
# 🎨 CONFIGURACIÓN Y ESTILO v6.1 (RESTAURADO)
# ==========================================
st.set_page_config(page_title="BETPLAY AI ANALYZER PRO", layout="wide")

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
        border-left: 6px solid #009345; display: flex; justify-content: space-between; align-items: center;
    }
    
    .stButton>button {
        width: 100%; background-color: #009345; color: white;
        border-radius: 10px; border: none; font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Funciones Core ---
def poisson_prob(lmbda, k):
    if lmbda <= 0: return 1.0 if k == 0 else 0.0
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

def calcular_o_u(lmbda, limite):
    prob_under = sum(poisson_prob(lmbda, k) for k in range(int(limite) + 1))
    return (1 - prob_under) * 100, prob_under * 100

# ==========================================
# 🛠️ SIDEBAR (ESTILO v6.0)
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 20px; background-color: #0e1629; border-radius: 15px; border: 1px solid #1e3a8a; margin-bottom: 10px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/0/06/Flag_of_Venezuela.svg" width="90" style="border-radius: 5px; margin-bottom: 10px;">
            <p style="color: #009345; font-size: 0.8rem; font-weight: bold; margin:0; letter-spacing: 2px;">ANALYTICS PRO</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 ACTUALIZAR DATOS API"):
        st.cache_data.clear()
        st.rerun()

    ligas = api.obtener_ligas()
    if ligas:
        liga_sel = st.selectbox("Seleccionar Liga", ligas, format_func=lambda x: x['nombre'])
        st.markdown(f'<div style="text-align: center; margin-bottom:15px;"><img src="{liga_sel.get("logo", "")}" width="45"></div>', unsafe_allow_html=True)

        equipos = api.obtener_equipos_liga(liga_sel['id'])
        
        if equipos:
            local_obj = st.selectbox("🏠 Local", equipos, index=0, format_func=lambda x: x['nombre'])
            visit_obj = st.selectbox("✈️ Visitante", equipos, index=1 if len(equipos) > 1 else 0, format_func=lambda x: x['nombre'])
            
            # Obtención de datos reales
            xh_f, xh_c = api.obtener_promedios_goles(local_obj['id'], liga_sel['id'])
            xa_f, xa_c = api.obtener_promedios_goles(visit_obj['id'], liga_sel['id'])
            
            # Cálculo de Lambdas (Expectativa de goles)
            l_h = (xh_f + xa_c) / 2
            l_a = (xa_f + xh_c) / 2
            
            st.markdown("---")
            l_corners = st.slider("Expectativa Córners", 5.0, 15.0, 9.5)
            l_tarjetas = st.slider("Expectativa Tarjetas", 0.0, 10.0, 4.2)
        else:
            st.error("⚠️ No se encontraron equipos para esta temporada.")
            st.stop()
    else: 
        st.stop()

# --- PROCESAMIENTO MATEMÁTICO ---
ph, pe, pa = 0, 0, 0
for i in range(10):
    for j in range(10):
        p = poisson_prob(l_h, i) * poisson_prob(l_a, j)
        if i > j: ph += p
        elif i == j: pe += p
        else: pa += p

total_p = ph + pe + pa
ph, pe, pa = ph/total_p, pe/total_p, pa/total_p

prob_btts_si = (1 - poisson_prob(l_h, 0)) * (1 - poisson_prob(l_a, 0))
prob_btts_no = 1 - prob_btts_si
btts_label = "BTTS: SÍ" if prob_btts_si >= 0.5 else "BTTS: NO"
btts_perc = prob_btts_si if prob_btts_si >= 0.5 else prob_btts_no
btts_color = "#009345" if prob_btts_si >= 0.5 else "#dc2626"

matriz_vals = np.zeros((6, 6))
for i in range(6):
    for j in range(6):
        matriz_vals[i, j] = poisson_prob(l_h, i) * poisson_prob(l_a, j) * 100

# ==========================================
# 🏟️ DASHBOARD PRINCIPAL
# ==========================================
st.markdown(f"""
    <div class="match-banner">
        <div style="display: flex; justify-content: space-around; align-items: center;">
            <div style="text-align: center; width: 30%;">
                <img src="{local_obj.get('logo','')}" width="95">
                <p style="color: white; font-weight: bold; margin-top: 10px;">{local_obj['nombre']}</p>
            </div>
            <div style="width: 30%; text-align: center;">
                <img src="{liga_sel.get('logo', '')}" width="50">
                <h1 style='color:white; margin:0;'>VS</h1>
                <p style='color:#009345; font-weight:bold; font-size: 0.8rem;'>{liga_sel['nombre']}</p>
            </div>
            <div style="text-align: center; width: 30%;">
                <img src="{visit_obj.get('logo','')}" width="95">
                <p style="color: white; font-weight: bold; margin-top: 10px;">{visit_obj['nombre']}</p>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["📈 PROYECCIONES", "🎯 LÍNEAS O/U", "📊 MATRIZ", "💰 COMPARADOR"])

with t1:
    st.markdown('<div class="betplay-header">Probabilidades Principales</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="mkt-card"><small>{local_obj["nombre"].upper()}</small><h2 style="color:#009345;">{ph*100:.1f}%</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mkt-card"><small>EMPATE</small><h2 style="color:#009345;">{pe*100:.1f}%</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mkt-card"><small>{visit_obj["nombre"].upper()}</small><h2 style="color:#009345;">{pa*100:.1f}%</h2></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="mkt-card"><small>{btts_label}</small><h2 style="color:{btts_color};">{btts_perc*100:.1f}%</h2></div>', unsafe_allow_html=True)

    st.markdown('<div class="betplay-header">⚔️ ÚLTIMOS ENFRENTAMIENTOS DIRECTOS (H2H)</div>', unsafe_allow_html=True)
    h2h_data = api.obtener_h2h(local_obj['id'], visit_obj['id'])
    if h2h_data:
        st.table(pd.DataFrame(h2h_data)) 
    else:
        st.info("No se registran enfrentamientos recientes.")

with t2:
    st.markdown('<div class="betplay-header">⚽ GOLES TOTALES</div>', unsafe_allow_html=True)
    g_lines = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
    cols_g = st.columns(6)
    for i, l in enumerate(g_lines):
        p_o, p_u = calcular_o_u(l_h + l_a, l)
        cols_g[i].markdown(f'<div class="mkt-card"><small>{l}</small><br><b>O: {p_o:.1f}%</b><br><small style="color:#94a3b8">U: {p_u:.1f}%</small></div>', unsafe_allow_html=True)

    st.markdown('<div class="betplay-header">🚩 CÓRNERS Y TARJETAS</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        p_o, p_u = calcular_o_u(l_corners, 9.5)
        st.markdown(f'<div class="mkt-card">CÓRNERS (9.5)<br><b>O: {p_o:.1f}%</b><br><small style="color:#94a3b8">U: {p_u:.1f}%</small></div>', unsafe_allow_html=True)
    with c2:
        p_o, p_u = calcular_o_u(l_tarjetas, 4.5)
        st.markdown(f'<div class="mkt-card">TARJETAS (4.5)<br><b>O: {p_o:.1f}%</b><br><small style="color:#94a3b8">U: {p_u:.1f}%</small></div>', unsafe_allow_html=True)

with t3:
    st.markdown('<div class="betplay-header">📍 MATRIZ DE MARCADORES EXACTOS</div>', unsafe_allow_html=True)
    fig = px.imshow(matriz_vals, text_auto=".1f", color_continuous_scale='Greens', x=['0','1','2','3','4','5'], y=['0','1','2','3','4','5'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

with t4:
    st.markdown('<div class="betplay-header">💰 COMPARADOR DE VALOR Y STAKE DINÁMICO</div>', unsafe_allow_html=True)
    with st.expander("📝 CONFIGURAR CUOTAS BETPLAY", expanded=True):
        c1, c2, c3 = st.columns(3)
        cuo_l = c1.number_input(f"Cuota {local_obj['nombre']}", 1.0, 20.0, 2.0, step=0.01)
        cuo_e = c1.number_input("Cuota Empate", 1.0, 20.0, 3.2, step=0.01)
        cuo_v = c1.number_input(f"Cuota {visit_obj['nombre']}", 1.0, 20.0, 3.5, step=0.01)
        
        cuo_bs = c2.number_input("BTTS SÍ", 1.0, 10.0, 1.8, step=0.01)
        cuo_bn = c2.number_input("BTTS NO", 1.0, 10.0, 1.9, step=0.01)
        
        bank = c3.number_input("Bankroll Actual ($)", value=100000)

    comparativa = [
        {"Mercado": "1 (Local)", "Prob": ph, "Cuota": cuo_l},
        {"Mercado": "X (Empate)", "Prob": pe, "Cuota": cuo_e},
        {"Mercado": "2 (Visita)", "Prob": pa, "Cuota": cuo_v},
        {"Mercado": "BTTS SÍ", "Prob": prob_btts_si, "Cuota": cuo_bs},
        {"Mercado": "BTTS NO", "Prob": prob_btts_no, "Cuota": cuo_bn},
    ]
    
    df_b = pd.DataFrame(comparativa)
    df_b["Edge %"] = ((df_b["Prob"] * df_b["Cuota"]) - 1) * 100
    
    # Cálculo de Stake Dinámico basado en Edge y Probabilidad
    def calcular_monto(row):
        if row["Edge %"] > 0:
            # Kelly simplificado (Stake proporcional al Edge)
            stake = (row["Edge %"] / 100) * (bank * 0.1) 
            return int(stake)
        return 0

    df_b["Stake Sugerido $"] = df_b.apply(calcular_monto, axis=1).apply(lambda x: f"${x:,}")
    
    # Formateo de tabla
    st.table(df_b.style.format({
        "Prob": "{:.1%}", "Cuota": "{:.2f}", "Edge %": "{:.1f}%"
    }))

st.caption("v6.1 - Sistema de Búsqueda 2026 Activo | Motor Estabilizado")







































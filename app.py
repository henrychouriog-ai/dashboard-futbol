import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import api  # Asegúrate de haber subido el api.py que te pasé antes
import math

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="BETPLAY AI", layout="wide")

# --- TUS ESTILOS ORIGINALES ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #050a14; }
    .main-header {
        background: linear-gradient(90deg, #004a99 0%, #050a14 100%);
        padding: 20px; border-radius: 10px; border-bottom: 4px solid #009345;
        text-align: center; margin-bottom: 20px;
    }
    .stMetric { background-color: #0e1629; padding: 10px; border-radius: 10px; border: 1px solid #1e293b; }
    </style>
""", unsafe_allow_html=True)

def poisson_prob(lmbda, k):
    if lmbda <= 0: return 1.0 if k == 0 else 0.0
    return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/13/Logo_de_la_Liga_Futve.png", width=100) # O tu logo
    st.title("BETPLAY AI")
    
    # Botón para forzar actualización si algo se pega
    if st.button("🔄 RECARGAR DATOS"):
        st.cache_data.clear()
        st.rerun()

    ligas = api.obtener_ligas()
    if ligas:
        # Quitamos códigos raros del nombre
        liga_sel = st.selectbox("Selecciona Liga", ligas, format_func=lambda x: x['nombre'])
        equipos = api.obtener_equipos_liga(liga_sel['id'])
        
        # IMPORTANTE: El 'key' dinámico asegura que los datos cambien
        col1, col2 = st.columns(2)
        with col1:
            local_obj = st.selectbox("🏠 Local", equipos, format_func=lambda x: x['nombre'], key=f"L_{liga_sel['id']}")
        with col2:
            visit_obj = st.selectbox("✈️ Visita", equipos, index=1 if len(equipos)>1 else 0, format_func=lambda x: x['nombre'], key=f"V_{liga_sel['id']}")
        
        # Obtener promedios reales
        xhf, xhc = api.obtener_promedios_goles(local_obj['id'], liga_sel['id'])
        xaf, xac = api.obtener_promedios_goles(visit_obj['id'], liga_sel['id'])
        
        # Expectativas de goles (Lambdas)
        lh, la = (xhf + xac)/2, (xaf + xhc)/2
        
        st.divider()
        l_corners = st.slider("Córners Previstos", 6.0, 16.0, 9.5)
        l_cards = st.slider("Tarjetas Previstas", 0.0, 10.0, 4.5)
    else:
        st.error("No se pudieron cargar las ligas.")
        st.stop()

# --- MOTOR DE CÁLCULO ---
ph, pe, pa = 0, 0, 0
matriz_vals = np.zeros((6, 6))
for i in range(6):
    for j in range(6):
        prob = poisson_prob(lh, i) * poisson_prob(la, j)
        matriz_vals[i, j] = prob * 100
        if i > j: ph += prob
        elif i == j: pe += prob
        else: pa += prob

# --- CUERPO PRINCIPAL (DISEÑO RESTAURADO) ---
st.markdown(f"""
    <div class="main-header">
        <img src="{liga_sel['logo']}" width="50"><br>
        <h1 style="color:white; margin:0;">{local_obj['nombre']} vs {visit_obj['nombre']}</h1>
        <p style="color:#009345;">{liga_sel['nombre']}</p>
    </div>
""", unsafe_allow_html=True)

# Reinstauramos tus pestañas originales
t1, t2, t3, t4 = st.tabs(["📈 PROYECCIONES", "🎯 LÍNEAS O/U", "📊 MATRIZ", "💰 COMPARADOR"])

with t1:
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Vitoria {local_obj['nombre']}", f"{ph*100:.1f}%")
    c2.metric("Empate", f"{pe*100:.1f}%")
    c3.metric(f"Victoria {visit_obj['nombre']}", f"{pa*100:.1f}%")
    
    st.subheader("⚔️ Enfrentamientos Directos (H2H)")
    h2h_data = api.obtener_h2h(local_obj['id'], visit_obj['id'])
    if h2h_data:
        st.table(pd.DataFrame(h2h_data))
    else:
        st.info("Sin datos de enfrentamientos previos.")

with t2:
    st.subheader("🎯 Probabilidades de Goles")
    col_a, col_b = st.columns(2)
    with col_a:
        for line in [0.5, 1.5, 2.5, 3.5]:
            p_under = sum(poisson_prob(lh+la, k) for k in range(int(line) + 1))
            st.write(f"**Over {line}:** {(1-p_under)*100:.1f}%")
    with col_b:
        for line in [0.5, 1.5, 2.5, 3.5]:
            p_under = sum(poisson_prob(lh+la, k) for k in range(int(line) + 1))
            st.write(f"**Under {line}:** {p_under*100:.1f}%")

with t3:
    fig = px.imshow(matriz_vals, text_auto=".1f", color_continuous_scale='Greens',
                    x=['0','1','2','3','4','5'], y=['0','1','2','3','4','5'])
    st.plotly_chart(fig, use_container_width=True)

with t4:
    st.subheader("💰 Calculadora de Valor (Kelly Criterion)")
    cuota_local = st.number_input("Cuota Local en Casa de Apuestas", 1.01, 20.0, 2.0)
    prob_real = ph
    edge = (prob_real * cuota_local) - 1
    
    if edge > 0:
        st.success(f"VALOR ENCONTRADO: {edge*100:.2f}%")
        kelly = (edge / (cuota_local - 1)) * 100
        st.write(f"Stake recomendado (Kelly): **{kelly/4:.2f}%** del bank.")
    else:
        st.error(f"No hay valor. Edge: {edge*100:.2f}%")







































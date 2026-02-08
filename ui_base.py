import streamlit as st

st.set_page_config(page_title="Dashboard Fútbol", layout="wide")

# -------------------------
# Estilos CSS (tema oscuro)
# -------------------------
st.markdown("""
<style>
body {
    background-color: #0f1115;
}
.block-container {
    padding-top: 1rem;
}
.card {
    background: #1c1f26;
    border-radius: 12px;
    padding: 15px;
    text-align: center;
    color: #00e5ff;
    box-shadow: 0 0 10px rgba(0,0,0,0.4);
}
.card-title {
    font-size: 14px;
    color: #00bcd4;
}
.card-value {
    font-size: 22px;
    color: #00ff88;
    font-weight: bold;
}
.panel {
    background: #1c1f26;
    border-radius: 16px;
    padding: 20px;
    min-height: 500px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Barra superior de ligas
# -------------------------
ligas = ["La Liga", "Bundesliga", "Ligue 1", "Serie A", "Premier", "Brasil", "Portugal", "Eredivisie"]

cols = st.columns(len(ligas))
for i, l in enumerate(ligas):
    cols[i].button(l)

st.divider()

# -------------------------
# Layout principal
# -------------------------
col_left, col_center, col_right = st.columns([2, 5, 2])

with col_left:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.selectbox("Seleccionar Equipo Local", ["Equipo A", "Equipo B", "Equipo C"])
    st.image("https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg", width=200)
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.selectbox("Seleccionar Equipo Visitante", ["Equipo X", "Equipo Y", "Equipo Z"])
    st.image("https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg", width=200)
    st.markdown("</div>", unsafe_allow_html=True)

with col_center:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)

    filas = [
        ["Primer Tiempo 0.5", "Prob Over 1.5", "Prob 2.5", "Prob 3.5", "Promedio Goles"],
        ["Ambos Marcan", "Rend. Local", "Rend. Visitante", "Favorito", "Resultado Probable"],
        ["Corners Over 9.5", "Promedio Corners", "Local Over 4.5", "Local Over 5.5", "Visita Over 4.5"],
        ["Visita Over 5.5", "Sugerencia Goles", "Intensidad Partido", "Estilo de Juego", "Momento de Goles"]
    ]

    for fila in filas:
        cols = st.columns(5)
        for i, titulo in enumerate(fila):
            with cols[i]:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">{titulo}</div>
                    <div class="card-value">0%</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


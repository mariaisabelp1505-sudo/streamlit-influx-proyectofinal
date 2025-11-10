import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import altair as alt
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard Industrial", page_icon="🏭", layout="wide")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
.main-header {
    font-size: 2.3rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 1.5rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.15);
}
.metric-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 3px 8px rgba(0,0,0,0.1);
}
.status-good {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: white; border-radius: 6px; padding: 0.3rem; font-weight:bold;
}
.status-warning {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white; border-radius: 6px; padding: 0.3rem; font-weight:bold;
}
.status-critical {
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
    color: white; border-radius: 6px; padding: 0.3rem; font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN PARA DATOS SIMULADOS ---
@st.cache_data
def generar_datos():
    fechas = pd.date_range('2024-09-20', '2024-09-22 23:59', freq='30min')
    np.random.seed(42)
    return pd.DataFrame({
        'Fecha': fechas,
        'Temperatura_Reactor_1': 250 + np.random.normal(0, 10, len(fechas)),
        'Presion_Sistema': 15 + np.random.normal(0, 2, len(fechas)),
        'Flujo_Entrada': 100 + np.random.normal(0, 5, len(fechas)),
        'Nivel_Tanque': 75 + np.random.normal(0, 8, len(fechas)),
        'Eficiencia_Proceso': 85 + np.random.normal(0, 5, len(fechas))
    })

df = generar_datos()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Controles del Sistema")
fecha = st.sidebar.date_input("📅 Selecciona Fecha", datetime(2024,9,21))
variables = st.sidebar.multiselect(
    "📊 Variables a visualizar",
    [c for c in df.columns if c != "Fecha"],
    default=['Temperatura_Reactor_1', 'Presion_Sistema', 'Flujo_Entrada', 'Nivel_Tanque']
)
rango = st.sidebar.slider("⏱️ Rango de Horas", 0, 24, (8, 20))
auto_refresh = st.sidebar.checkbox("🔄 Actualizar automáticamente (cada 30s)")

if auto_refresh:
    time.sleep(1)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.success("🟢 Sistema en línea")
st.sidebar.info(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# --- CABECERA ---
st.markdown('<h1 class="main-header">🏭 Dashboard de Monitoreo Industrial</h1>', unsafe_allow_html=True)
st.divider()

# --- FILTRO DE DATOS ---
datos_filtrados = df[df['Fecha'].dt.date == fecha]

# --- MÉTRICAS PRINCIPALES ---
st.markdown("## 📊 Métricas en Tiempo Real")
cols = st.columns(4)
metricas = [
    ("🌡️ Temperatura Reactor", "Temperatura_Reactor_1", "°C"),
    ("⚙️ Presión Sistema", "Presion_Sistema", "Bar"),
    ("💧 Flujo Entrada", "Flujo_Entrada", "L/min"),
    ("📦 Nivel Tanque", "Nivel_Tanque", "%")
]

valores_actuales = datos_filtrados.iloc[-1] if not datos_filtrados.empty else None

for i, (titulo, var, unidad) in enumerate(metricas):
    with cols[i]:
        if valores_actuales is not None:
            valor = valores_actuales[var]
            delta = np.random.uniform(-2, 2)
            # estado visual
            if var == 'Temperatura_Reactor_1':
                clase = 'status-good' if 240 <= valor <= 260 else 'status-warning'
            elif var == 'Presion_Sistema':
                clase = 'status-good' if 12 <= valor <= 18 else 'status-warning'
            else:
                clase = 'status-warning' if np.random.rand() > 0.5 else 'status-good'

            st.metric(titulo, f"{valor:.1f} {unidad}", f"{delta:+.1f}")
            st.markdown(f'<div class="{clase}">{"Bueno" if "good" in clase else "Advertencia"}</div>', unsafe_allow_html=True)
        else:
            st.info("Sin datos")

st.divider()

# --- GRÁFICOS ---
with st.expander("📈 Tendencias de Variables", expanded=True):






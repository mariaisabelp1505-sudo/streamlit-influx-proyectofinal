import streamlit as st
import pandas as pd
import plotly.express as px
from influxdb_client import InfluxDBClient
from datetime import datetime

# --- Parámetros de conexión ---
INFLUXDB_URL = st.secrets["INFLUXDB_URL"]
INFLUXDB_TOKEN = st.secrets["INFLUXDB_TOKEN"]
INFLUXDB_ORG = st.secrets["INFLUXDB_ORG"]
INFLUXDB_BUCKET = st.secrets["INFLUXDB_BUCKET"]

# --- Inicializar cliente ---
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

# --- Configuración lateral ---
st.sidebar.header("Filtros")
days = st.sidebar.slider("Rango de tiempo (días)", 1, 30, 3)

st.title("🏭 Tablero de Monitoreo Industrial")
st.write("Datos de sensores *DHT22* y *MPU6050*")

# --- Función para consultar datos ---
def query_data(measurement, fields):
    fields_filter = " or ".join([f'r._field == "{f}"' for f in fields])
    query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -{days}d)
      |> filter(fn: (r) => r._measurement == "{measurement}")
      |> filter(fn: (r) => {fields_filter})
    '''
    tables = query_api.query(org=INFLUXDB_ORG, query=query)
    data = []
    for table in tables:
        for record in table.records:
            data.append((record.get_time(), record.get_field(), record.get_value()))

    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data, columns=["time", "field", "value"])
    df = df.pivot(index="time", columns="field", values="value").reset_index()
    return df

# --- Sensor DHT22 ---
fields_dht = ["temperatura", "humedad", "sensacion_termica"]
df_dht = query_data("studio-dht22", fields_dht)

# =========================
# 📊 WIDGETS EN TIEMPO REAL
# =========================
st.markdown("### 🔴 Monitoreo en Tiempo Real - Sensor DHT22")

if not df_dht.empty:
    last_row = df_dht.iloc[-1]
    last_time = pd.to_datetime(last_row["time"]).strftime("%Y-%m-%d %H:%M:%S")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Temperatura (°C)", f"{last_row['temperatura']:.2f}")
    col2.metric("💧 Humedad (%)", f"{last_row['humedad']:.2f}")
    col3.metric("🔥 Sensación Térmica (°C)", f"{last_row['sensacion_termica']:.2f}")
    col4.metric("🕒 Última Lectura", last_time)

else:
    st.warning("No hay datos disponibles del sensor DHT22 para este rango de tiempo.")

st.divider()

# --- Gráfica DHT22 ---
st.subheader("📈 Sensor DHT22 (Temperatura y Humedad)")
if not df_dht.empty:
    fig_dht = px.line(df_dht, x="time", y=fields_dht, title="Lecturas DHT22")
    st.plotly_chart(fig_dht, use_container_width=True)
    st.write("*Métricas DHT22*")
    st.dataframe(df_dht.describe().T[["mean", "min", "max"]])

# --- Sensor MPU6050 ---
st.subheader("📉 Sensor MPU6050 (Vibraciones y Aceleración)")
fields_mpu = ["accel_x", "accel_y", "accel_z"]
df_mpu = query_data("mpu6050", fields_mpu)

if not df_mpu.empty:
    fig_mpu = px.line(df_mpu, x="time", y=fields_mpu, title="Lecturas MPU6050")
    st.plotly_chart(fig_mpu, use_container_width=True)
    st.write("*Métricas MPU6050*")
    st.dataframe(df_mpu.describe().T[["mean", "min", "max"]])
else:
    st.warning("No hay datos disponibles del sensor MPU6050 para este rango de tiempo.")

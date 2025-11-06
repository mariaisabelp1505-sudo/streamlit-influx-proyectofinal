import streamlit as st
import pandas as pd
import plotly.express as px
from influxdb_client import InfluxDBClient

# --- Configuración general ---
st.set_page_config(page_title="Monitoreo Industrial", layout="wide")

st.title("Tablero de Monitoreo Industrial")
st.write("Visualización de datos en tiempo real de los sensores **DHT22** y **MPU6050**")

# --- Conexión a InfluxDB ---
INFLUXDB_URL = st.secrets["INFLUXDB_URL"]
INFLUXDB_TOKEN = st.secrets["INFLUXDB_TOKEN"]
INFLUXDB_ORG = st.secrets["INFLUXDB_ORG"]
INFLUXDB_BUCKET = st.secrets["INFLUXDB_BUCKET"]

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

# --- Filtros laterales ---
st.sidebar.header(" Filtros")
days = st.sidebar.slider("Rango de tiempo (días)", 1, 30, 3)

# --- Función para consultar datos ---
@st.cache_data(ttl=300)
def query_data(measurement, fields):
    try:
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
        df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
        return df

    except Exception as e:
        st.error(f"Error al consultar InfluxDB: {e}")
        return pd.DataFrame()

# --- Sensor DHT22 ---
st.subheader(" Sensor DHT22 (Temperatura y Humedad)")
fields_dht = ["temperatura", "humedad", "sensacion_termica"]
df_dht = query_data("studio-dht22", fields_dht)

if not df_dht.empty:
    fig_dht = px.line(df_dht, x="time", y=fields_dht, title="Lecturas DHT22")
    fig_dht.update_xaxes(title="Tiempo")
    fig_dht.update_yaxes(title="Valor")
    st.plotly_chart(fig_dht, use_container_width=True)

    st.write("** Métricas DHT22**")
    st.dataframe(df_dht.describe().T[["mean", "min", "max"]])
else:
    st.warning(" No hay datos disponibles del sensor DHT22 para este rango de tiempo.")

# --- Sensor MPU6050 ---
st.subheader(" Sensor MPU6050 (Vibraciones y Aceleración)")
fields_mpu = ["accel_x", "accel_y", "accel_z"]
df_mpu = query_data("mpu6050", fields_mpu)

if not df_mpu.empty:
    fig_mpu = px.line(df_mpu, x="time", y=fields_mpu, title="Lecturas MPU6050")
    fig_mpu.update_xaxes(title="Tiempo")
    fig_mpu.update_yaxes(title="Aceleración (m/s²)")
    st.plotly_chart(fig_mpu, use_container_width=True)

    st.write("**Métricas MPU6050**")
    st.dataframe(df_mpu.describe().T[["mean", "min", "max"]])
else:
    st.warning("No hay datos disponibles del sensor MPU6050 para este rango de tiempo.")

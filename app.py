import streamlit as st
import pandas as pd
import plotly.express as px
from influxdb_client import InfluxDBClient

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


st.title(" Tablero de Monitoreo Industrial")
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
st.subheader(" Sensor DHT22 (Temperatura y Humedad)")
fields_dht = ["temperatura", "humedad", "sensacion_termica"]
df_dht = query_data("studio-dht22", fields_dht)

if not df_dht.empty:
    fig_dht = px.line(df_dht, x="time", y=fields_dht, title="Lecturas DHT22")
    st.plotly_chart(fig_dht, use_container_width=True)

    st.write("*Métricas DHT22*")
    st.dataframe(df_dht.describe().T[["mean", "min", "max"]])
else:
    st.warning("No hay datos disponibles del sensor DHT22 para este rango de tiempo.")

# --- Sensor MPU6050 ---
st.subheader(" Sensor MPU6050 (Vibraciones y Aceleración)")
fields_mpu = ["accel_x", "accel_y", "accel_z"]
df_mpu = query_data("mpu6050", fields_mpu)

if not df_mpu.empty:
    fig_mpu = px.line(df_mpu, x="time", y=fields_mpu, title="Lecturas MPU6050")
    st.plotly_chart(fig_mpu, use_container_width=True)

    st.write("*Métricas MPU6050*")
    st.dataframe(df_mpu.describe().T[["mean", "min", "max"]])
else:
    st.warning("No hay datos disponibles del sensor MPU6050 para este rango de tiempo.")

# Función para determinar el estado de una variable
def obtener_estado_variable(valor, variable):
    estados = {
        'Temperatura_Reactor_1': {'bueno': (240, 260), 'advertencia': (230, 270), 'critico': (0, 230)},
        'Presion_Sistema': {'bueno': (12, 18), 'advertencia': (10, 20), 'critico': (0, 10)},
        'Flujo_Entrada': {'bueno': (90, 110), 'advertencia': (80, 120), 'critico': (0, 80)},
        'Nivel_Tanque': {'bueno': (60, 90), 'advertencia': (40, 100), 'critico': (0, 40)},
        'pH_Proceso': {'bueno': (6.8, 7.6), 'advertencia': (6.5, 8.0), 'critico': (0, 6.5)},
        'Eficiencia_Proceso': {'bueno': (80, 100), 'advertencia': (70, 80), 'critico': (0, 70)}
    }
    
    if variable in estados:
        if estados[variable]['bueno'][0] <= valor <= estados[variable]['bueno'][1]:
            return 'Bueno', 'status-good'
        elif estados[variable]['advertencia'][0] <= valor <= estados[variable]['advertencia'][1]:
            return 'Advertencia', 'status-warning'
        else:
            return 'Crítico', 'status-critical'
    
    return 'Desconocido', 'status-warning'

# Título principal
st.markdown('<h1 class="main-header">🏭 Dashboard de Control Industrial</h1>', unsafe_allow_html=True)

# Cargar datos
df = generar_datos_industriales()

# Sidebar para controles
st.sidebar.title("⚙️ Controles del Sistema")

# Selector de fecha
fecha_min = df['Fecha'].min().date()
fecha_max = df['Fecha'].max().date()
fecha_actual = datetime.now().date()

# Si la fecha actual está fuera del rango, usar la fecha máxima disponible
if fecha_actual < fecha_min or fecha_actual > fecha_max:
    fecha_por_defecto = fecha_max
else:
    fecha_por_defecto = fecha_actual

fecha_seleccionada = st.sidebar.date_input(
    "Seleccionar Fecha",
    value=fecha_por_defecto,
    min_value=fecha_min,
    max_value=fecha_max
)

# Selector de variables
variables_disponibles = [col for col in df.columns if col != 'Fecha']
variables_seleccionadas = st.sidebar.multiselect(
    "Variables a Mostrar",
    variables_disponibles,
    default=variables_disponibles[:4]
)



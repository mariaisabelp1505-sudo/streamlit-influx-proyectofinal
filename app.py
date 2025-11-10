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
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Info del Sistema")
st.sidebar.info(f"Total de registros: {len(df):,}")
st.sidebar.info(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

if auto_refresh:
    time.sleep(1)
    st.rerun()

# Filtrar datos según la fecha seleccionada
datos_filtrados = df[df['Fecha'].dt.date == fecha_seleccionada]

if not datos_filtrados.empty:
    # Estado general del sistema
    st.markdown("## 🚦 Estado General del Sistema")
    
    col_estado1, col_estado2, col_estado3, col_estado4 = st.columns(4)
    
    with col_estado1:
        st.markdown('<div class="alert-low"><strong>🟢 Sistemas Operativos</strong><br>6/8 variables normales</div>', unsafe_allow_html=True)
    
    with col_estado2:
        st.markdown('<div class="alert-medium"><strong>🟡 Advertencias</strong><br>2 variables en alerta</div>', unsafe_allow_html=True)
    
    with col_estado3:
        st.markdown('<div class="alert-low"><strong>⚡ Eficiencia</strong><br>87.3% promedio</div>', unsafe_allow_html=True)
    
    with col_estado4:
        st.markdown('<div class="alert-low"><strong>🔧 Uptime</strong><br>99.2% disponibilidad</div>', unsafe_allow_html=True)

    # Métricas en tiempo real
    st.markdown("## 📊 Métricas en Tiempo Real")
    
    cols = st.columns(4)
    valores_actuales = datos_filtrados.iloc[-1]  # Último valor del día
    
    metricas = [
        ("Temperatura Reactor", "Temperatura_Reactor_1", "°C"),
        ("Presión Sistema", "Presion_Sistema", "Bar"),
        ("Flujo Entrada", "Flujo_Entrada", "L/min"),
        ("Nivel Tanque", "Nivel_Tanque", "%")
    ]
    
    for i, (nombre, variable, unidad) in enumerate(metricas):
        if variable in valores_actuales:
            valor = valores_actuales[variable]
            estado, clase_css = obtener_estado_variable(valor, variable)
            
            with cols[i]:
                st.metric(
                    label=f"{nombre}",
                    value=f"{valor:.1f} {unidad}",
                    delta=f"{np.random.uniform(-2, 2):.1f}"
                )
                st.markdown(f'<div class="{clase_css}">{estado}</div>', unsafe_allow_html=True)




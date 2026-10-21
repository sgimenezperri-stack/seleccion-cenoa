import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="Dashboard de Selección | Cenoa", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stDataFrame { font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga y procesamiento de datos
@st.cache_data(ttl=600)
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS80spSAFpaYNM_WigjJoBXrpOdwVo9TpR1Eqf3Fyrjsa8IDHU1AJnmq2tvBCMgS4Daxb4vt3cIyKZ4/pub?output=csv"
    try:
        df = pd.read_csv(sheet_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# Nombres de columnas esperados (Ajustar a las cabeceras exactas del Google Sheet)
COL_ESTADO = "Estado" 
COL_DEMORA = "Condicion_Demora" 
COL_EMPRESA = "Empresa" 
COL_AREA = "Area" 
COL_MOD_CONTRACTUAL = "Mod_Contractual"
COL_TIPO_BUSQUEDA = "Tipo Busqueda"
COL_DIAS_DEMORA = "Dias Demora"
COL_FECHA = "Recep.Sol." 
COL_POSICION = "Búsquedas" # <-- AJUSTAR AL NOMBRE EXACTO DE TU COLUMNA F

# Datos dummy en caso de que el sheet esté vacío o no coincidan las columnas aún
if df.empty or COL_EMPRESA not in df.columns:
    df = pd.DataFrame({
        COL_ESTADO: ["EN PROCESO", "FINALIZADA", "EN PROCESO", "ERROR", "FINALIZADA"] * 4,
        COL_DEMORA: ["Abierta Demorada", "Finalizada Demorada", "Finalizada Ok", "Abierta Demorada", "Finalizada Ok"] * 4,
        COL_EMPRESA: ["AUTOCIEL", "AUTOLUX", "CHANGO CAR", "AUTOCIEL", "VOGE"] * 4,
        COL_AREA: ["ADMINISTRACION", "COMERCIAL", "GENERAL", "POSVENTA", "COMERCIAL"] * 4,
        COL_MOD_CONTRACTUAL: ["Dentro de Convenio", "Fuera de Convenio", "Practica Profesional", "Dentro de Convenio", "Fuera de Convenio"] * 4,
        COL_TIPO_BUSQUEDA: ["Posventa", "Administración concesionarios", "Gerencias - Sub", "Asesores comerciales", "Staff (Analistas)"] * 4,
        COL_POSICION: ["Gerente Comercial", "Administrativo Integral", "Practicante Garantias", "Practicante Tecnico", "Asesor de Ventas"] * 4,
        COL_DIAS_DEMORA: [15, -5, 45, 10, 30] * 4,
        "N° Ticket": [9816078, 676, 671, 672, 673] * 4,
        "Provincia": ["JUJUY CAPITAL", "SALTA CAPITAL"] * 10,
        COL_FECHA: ["4/9/2026", "5/29/2026", "1/15/2026", "10/10/2025", "8/20/2026"] * 4
    })

# Procesamiento de Fechas para Filtros
df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors='coerce')
df['Año'] = df[COL_FECHA].dt.year.fillna(datetime.now().year).astype(int)

# Diccionario para nombres de meses en español
meses_espanol = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}
df['Mes_Num'] = df[COL_FECHA].dt.month
df['Mes'] = df['Mes_Num'].map(meses_espanol).fillna('Sin fecha')

# 3. Encabezado con Responsable
col_tit1, col_tit2 = st.columns([3, 1])
with col_tit1:
    st.title("Tiempos de Cobertura y Selección")
with col_tit2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Resp. Actual:** Solana Giménez<br>**Últ. Actual:** Tiempo Real", unsafe_allow_html=True)

# 4. Filtros Superiores Dinámicos
col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
with col_f1:
    estado_filtro = st.multiselect("ESTADO DEL PROCESO", df[COL_ESTADO].dropna().unique(), default=df[COL_ESTADO].dropna().unique())
with col_f2:
    empresa_filtro = st.multiselect("EMPRESA", df[COL_EMPRESA].dropna().unique(), default=df[COL_EMPRESA].dropna().unique())
with col_f3:
    area_filtro = st.multiselect("ÁREA", df[COL_AREA].dropna().unique(), default=df[COL_AREA].dropna().unique())
with col_f4:
    año_filtro = st.multiselect("AÑO", sorted(df['Año'].unique(), reverse=True), default=sorted(df['Año'].unique(), reverse=True))
with col_f5:
    meses_disponibles = df[['Mes_Num', 'Mes']].drop_duplicates().sort_values('Mes_Num')['Mes'].tolist()
    mes_filtro = st.multiselect("MES", meses_disponibles, default=meses_disponibles)

# 5. Aplicar todos los filtros (Lógica condicional)
df_filtered = df.copy()

if estado_filtro:
    df_filtered = df_filtered[df_filtered[COL_ESTADO].isin(estado_filtro)]
if empresa_filtro:
    df_filtered = df_filtered[df_filtered[COL_EMPRESA].isin(empresa_filtro)]
if area_filtro:
    df_filtered = df_filtered[df_filtered[COL_AREA].isin(area_filtro)]
if año_filtro:
    df_filtered = df_filtered[df_filtered['Año'].isin(año_filtro)]
if mes_filtro:
    df_filtered = df_filtered[df_filtered['Mes'].isin(mes_filtro)]

st.markdown("---")

# 6. Primera Fila de Gráficos: Dona y Cascada
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("**Distribución de Búsquedas**")
    if not df_filtered.empty:
        df_demora = df_filtered[COL_DEMORA].value_counts().reset_index()
        df_dem

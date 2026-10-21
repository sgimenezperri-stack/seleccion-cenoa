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
        df.columns = df.columns.str.strip() # Limpia espacios accidentales
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

# Datos dummy preventivos
if df.empty or COL_EMPRESA not in df.columns:
    df = pd.DataFrame({
        COL_ESTADO: ["EN PROCESO", "FINALIZADA"] * 10,
        COL_DEMORA: ["Abierta Demorada", "Finalizada Ok"] * 10,
        COL_EMPRESA: ["AUTOCIEL", "AUTOLUX"] * 10,
        COL_AREA: ["COMERCIAL", "POSVENTA"] * 10,
        COL_MOD_CONTRACTUAL: ["Dentro de Convenio", "Fuera de Convenio"] * 10,
        COL_TIPO_BUSQUEDA: ["Posventa", "Administración concesionarios"] * 10,
        COL_POSICION: ["Gerente Comercial", "Administrativo Integral"] * 10,
        COL_DIAS_DEMORA: [15, -5] * 10,
        "N° Ticket": [9816078, 676] * 10,
        "Provincia": ["JUJUY CAPITAL", "SALTA CAPITAL"] * 10,
        COL_FECHA: ["4/9/2026", "5/29/2026"] * 10
    })

# Procesamiento de Fechas
if COL_FECHA in df.columns:
    df[COL_FECHA] = pd.to_datetime(df[COL_FECHA], errors='coerce')
    df['Año'] = df[COL_FECHA].dt.year.fillna(datetime.now().year).astype(int)
    meses_espanol = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes_Num'] = df[COL_FECHA].dt.month
    df['Mes'] = df['Mes_Num'].map(meses_espanol).fillna('Sin fecha')
else:
    df['Año'] = 2026
    df['Mes'] = 'Sin fecha'
    df['Mes_Num'] = 1

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
    estado_opts = df[COL_ESTADO].dropna().unique() if COL_ESTADO in df.columns else []
    estado_filtro = st.multiselect("ESTADO", estado_opts, default=estado_opts)
with col_f2:
    empresa_opts = df[COL_EMPRESA].dropna().unique() if COL_EMPRESA in df.columns else []
    empresa_filtro = st.multiselect("EMPRESA", empresa_opts, default=empresa_opts)
with col_f3:
    area_opts = df[COL_AREA].dropna().unique() if COL_AREA in df.columns else []
    area_filtro = st.multiselect("ÁREA", area_opts, default=area_opts)
with col_f4:
    año_filtro = st.multiselect("AÑO", sorted(df['Año'].unique(), reverse=True), default=sorted(df['Año'].unique(), reverse=True))
with col_f5:
    meses_disponibles = df[['Mes_Num', 'Mes']].drop_duplicates().sort_values('Mes_Num')['Mes'].tolist()
    mes_filtro = st.multiselect("MES", meses_disponibles, default=meses_disponibles)

# 5. Aplicar Filtros
df_filtered = df.copy()
if estado_filtro and COL_ESTADO in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[COL_ESTADO].isin(estado_filtro)]
if empresa_filtro and COL_EMPRESA in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[COL_EMPRESA].isin(empresa_filtro)]
if area_filtro and COL_AREA in df_filtered.columns:
    df_filtered = df_filtered[df_filtered[COL_AREA].isin(area_filtro)]
if año_filtro:
    df_filtered = df_filtered[df_filtered['Año'].isin(año_filtro)]
if mes_filtro:
    df_filtered = df_filtered[df_filtered['Mes'].isin(mes_filtro)]

st.markdown("---")

# 6. Primera Fila de Gráficos
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("**Distribución de Búsquedas**")
    if not df_filtered.empty and COL_DEMORA in df_filtered.columns:
        df_demora = df_filtered[COL_DEMORA].value_counts().reset_index()
        df_demora.columns = [COL_DEMORA, 'Cantidad']
        color_map_demora = {"Abierta Demorada": "#4b8bbe", "Finalizada Demorada": "#132c66", "Finalizada Ok": "#ed7d31"}
        fig_dona = px.pie(df_demora, values='Cantidad', names=COL_DEMORA, hole=0.6, color=COL_DEMORA, color_discrete_map=color_map_demora)
        fig_dona.update_traces(textposition='outside', textinfo='percent+label')
        fig_dona.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
        st.plotly_chart(fig_dona, use_container_width=True)
    else:
        st.warning(f"Revisar columna: {COL_DEMORA}")

with col2:
    st.markdown("**Búsquedas por Empresa**")
    if not df_filtered.empty and COL_EMPRESA in df_filtered.columns:
        df_empresa = df_filtered[COL_EMPRESA].value_counts().reset_index()
        df_empresa.columns = [COL_EMPRESA, 'Cantidad']
        fig_waterfall = go.Figure(go.Waterfall(
            name="Empresas", orientation="v", measure=["relative"] * len(df_empresa) + ["total"],
            x=df_empresa[COL_EMPRESA].tolist() + ["Total"], y=df_empresa['Cantidad'].tolist() + [df_empresa['Cantidad'].sum()],
            text=df_empresa['Cantidad'].tolist() + [df_empresa['Cantidad'].sum()], textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}}, decreasing={"marker": {"color": "#ed7d31"}}, increasing={"marker": {"color": "#ed7d31"}}, totals={"marker": {"color": "#4b8bbe"}}
        ))
        fig_waterfall.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=300, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_waterfall, use_container_width=True)
    else:
        st.warning(f"Revisar columna: {COL_EMPRESA}")

# 7. Segunda Fila de Gráficos
col3, col4, col5 = st.columns([2, 1.5, 0.5])

with col3:
    st.markdown("**Búsquedas por Área**")
    if not df_filtered.empty and COL_AREA in df_filtered.columns:
        df_area = df_filtered[COL_AREA].value_counts().reset_index()
        df_area.columns = [COL_AREA, 'Cantidad']
        fig_bar = px.bar(df_area, x='Cantidad', y=[1]*len(df_area), color=COL_AREA, orientation='h', text='Cantidad', color_discrete_sequence=['#132c66', '#ed7d31', '#7030a0', '#00b0f0'])
        fig_bar.update_traces(textposition='inside')
        fig_bar.update_layout(barmode='stack', showlegend=True, yaxis=dict(showticklabels=False, title=''), xaxis=dict(showticklabels=False, title=''), margin=dict(t=0, b=0, l=0, r=0), height=150, plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning(f"Revisar columna: {COL_AREA}")

with col5:
    st.markdown("**Filtrar por:**")
    opciones_filtro = ["Mod. Contractual", "Provincia", "Estado"]
    filtro_seleccionado = st.radio("", opciones_filtro, label_visibility="collapsed")

with col4:
    st.markdown(f"**Búsquedas por {filtro_seleccionado}**")
    columna_dinamica = COL_MOD_CONTRACTUAL if filtro_seleccionado == "Mod. Contractual" else filtro_seleccionado
    if not df_filtered.empty and columna_dinamica in df_filtered.columns:
        df_dinamico = df_filtered[columna_dinamica].value_counts().reset_index()
        df_dinamico.columns = [columna_dinamica, 'Cantidad']
        fig_pie_dinamico = px.pie(df_dinamico, values='Cantidad', names=columna_dinamica, color_discrete_sequence=['#4b8bbe', '#132c66', '#ed7d31'])
        fig_pie_dinamico.update_traces(textposition='outside', textinfo='percent')
        fig_pie_dinamico.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
        st.plotly_chart(fig_pie_dinamico, use_container_width=True)
    else:
        st.warning(f"Revisar columna: {columna_dinamica}")

st.markdown("---")

# 8. Tablas de Detalle
st.markdown("**Resumen por Tipo de Búsqueda**")
if not df_filtered.empty and COL_TIPO_BUSQUEDA in df_filtered.columns:
    df_resumen = df_filtered.groupby(COL_TIPO_BUSQUEDA).agg(Q_Busq=('N° Ticket', 'count'), Dias_Demora_Promedio=(COL_DIAS_DEMORA, 'mean')).reset_index()
    df_resumen['Dias_Demora_Promedio'] = df_resumen['Dias_Demora_Promedio'].round(0)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

st.markdown("**Detalle Operativo**")
def color_demora(val):
    if isinstance(val, (int, float)): return 'background-color: #ffcccc' if val > 0 else 'background-color: #ccffcc'
    return ''

columnas_mostrar = [col for col in ["N° Ticket", COL_POSICION, COL_TIPO_BUSQUEDA, COL_EMPRESA, "Provincia", COL_FECHA, COL_ESTADO, COL_DIAS_DEMORA] if col in df_filtered.columns]
if not df_filtered.empty:
    st.dataframe(df_filtered[columnas_mostrar].style.map(color_demora, subset=[COL_DIAS_DEMORA] if COL_DIAS_DEMORA in columnas_mostrar else []), use_container_width=True, hide_index=True)

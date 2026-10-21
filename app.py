import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Dashboard de Selección | Cenoa", layout="wide", initial_sidebar_state="collapsed")

# Estilos CSS personalizados para ajustar márgenes y dar aspecto de Power BI
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    h1, h2, h3 { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stDataFrame { font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga de datos
@st.cache_data(ttl=600)
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS80spSAFpaYNM_WigjJoBXrpOdwVo9TpR1Eqf3Fyrjsa8IDHU1AJnmq2tvBCMgS4Daxb4vt3cIyKZ4/pub?output=csv"
    try:
        df = pd.read_csv(sheet_url)
        # Normalizar nombres de columnas para evitar errores de espacios
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# Nombres de columnas esperados (Ajusta estos strings a los de tu Google Sheet)
COL_ESTADO = "Estado" # Ej: En proceso, Finalizada
COL_DEMORA = "Condicion_Demora" # Ej: Abierta Demorada, Finalizada Ok
COL_EMPRESA = "Empresa" # Ej: Autociel, Autolux
COL_AREA = "Area" # Ej: Comercial, Posventa
COL_MOD_CONTRACTUAL = "Mod_Contractual"
COL_TIPO_BUSQUEDA = "Tipo Busqueda"
COL_DIAS_DEMORA = "Dias Demora"

# Si el df está vacío o no conecta, creamos datos dummy estructurales para que veas el diseño
if df.empty or COL_EMPRESA not in df.columns:
    df = pd.DataFrame({
        COL_ESTADO: ["EN PROCESO", "FINALIZADA", "EN PROCESO", "ERROR", "FINALIZADA"] * 4,
        COL_DEMORA: ["Abierta Demorada", "Finalizada Demorada", "Finalizada Ok", "Abierta Demorada", "Finalizada Ok"] * 4,
        COL_EMPRESA: ["AUTOCIEL", "AUTOLUX", "CHANGO CAR", "AUTOCIEL", "VOGE"] * 4,
        COL_AREA: ["ADMINISTRACION", "COMERCIAL", "GENERAL", "POSVENTA", "COMERCIAL"] * 4,
        COL_MOD_CONTRACTUAL: ["Dentro de Convenio", "Fuera de Convenio", "Practica Profesional", "Dentro de Convenio", "Fuera de Convenio"] * 4,
        COL_TIPO_BUSQUEDA: ["Posventa", "Administración concesionarios", "Gerencias - Sub", "Asesores comerciales", "Staff (Analistas)"] * 4,
        COL_DIAS_DEMORA: [15, -5, 45, 10, 30] * 4,
        "N° Ticket": [9816078, 676, 671, 672, 673] * 4,
        "Provincia": ["JUJUY CAPITAL", "SALTA CAPITAL"] * 10
    })

# 3. Encabezado y Filtros Superiores
st.title("Tiempos de Cobertura y Selección")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    estado_filtro = st.multiselect("ESTADO DEL PROCESO", df[COL_ESTADO].unique(), default=df[COL_ESTADO].unique())
with col_f2:
    empresa_filtro = st.multiselect("EMPRESA", df[COL_EMPRESA].unique(), default=df[COL_EMPRESA].unique())
with col_f3:
    area_filtro = st.multiselect("ÁREA", df[COL_AREA].unique(), default=df[COL_AREA].unique())

# Aplicar filtros
df_filtered = df[
    (df[COL_ESTADO].isin(estado_filtro)) & 
    (df[COL_EMPRESA].isin(empresa_filtro)) &
    (df[COL_AREA].isin(area_filtro))
]

st.markdown("---")

# 4. Primera Fila de Gráficos: Dona y Cascada
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("**Distribución de Búsquedas: Demoras vs. Sin Demoras**")
    df_demora = df_filtered[COL_DEMORA].value_counts().reset_index()
    df_demora.columns = [COL_DEMORA, 'Cantidad']
    
    color_map_demora = {
        "Abierta Demorada": "#4b8bbe", 
        "Finalizada Demorada": "#132c66", 
        "Finalizada Ok": "#ed7d31"
    }
    
    fig_dona = px.pie(df_demora, values='Cantidad', names=COL_DEMORA, hole=0.6,
                      color=COL_DEMORA, color_discrete_map=color_map_demora)
    fig_dona.update_traces(textposition='outside', textinfo='percent+label')
    fig_dona.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig_dona, use_container_width=True)

with col2:
    st.markdown("**Búsquedas por Empresa**")
    df_empresa = df_filtered[COL_EMPRESA].value_counts().reset_index()
    df_empresa.columns = [COL_EMPRESA, 'Cantidad']
    
    fig_waterfall = go.Figure(go.Waterfall(
        name="Empresas", orientation="v",
        measure=["relative"] * len(df_empresa) + ["total"],
        x=df_empresa[COL_EMPRESA].tolist() + ["Total"],
        y=df_empresa['Cantidad'].tolist() + [df_empresa['Cantidad'].sum()],
        text=df_empresa['Cantidad'].tolist() + [df_empresa['Cantidad'].sum()],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#ed7d31"}},
        increasing={"marker": {"color": "#ed7d31"}},
        totals={"marker": {"color": "#4b8bbe"}}
    ))
    fig_waterfall.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=300, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_waterfall, use_container_width=True)

# 5. Segunda Fila de Gráficos: Barras Apiladas y Gráfico Circular Dinámico
col3, col4, col5 = st.columns([2, 1.5, 0.5])

with col3:
    st.markdown("**Búsquedas por Área**")
    df_area = df_filtered[COL_AREA].value_counts().reset_index()
    df_area.columns = [COL_AREA, 'Cantidad']
    # Gráfico de barras horizontales simulando el apilado del 100%
    fig_bar = px.bar(df_area, x='Cantidad', y=[1]*len(df_area), color=COL_AREA, 
                     orientation='h', text='Cantidad',
                     color_discrete_sequence=['#132c66', '#ed7d31', '#7030a0', '#00b0f0'])
    fig_bar.update_traces(textposition='inside')
    fig_bar.update_layout(barmode='stack', showlegend=True, 
                          yaxis=dict(showticklabels=False, title=''),
                          xaxis=dict(showticklabels=False, title=''),
                          margin=dict(t=0, b=0, l=0, r=0), height=150, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_bar, use_container_width=True)

with col5:
    st.markdown("**Filtrar Gráfico por:**")
    # Selector dinámico como en la imagen
    opciones_filtro = ["Mod. Contractual", "Provincia", "Estado"]
    filtro_seleccionado = st.radio("", opciones_filtro, label_visibility="collapsed")

with col4:
    st.markdown(f"**Búsquedas por {filtro_seleccionado}**")
    # Mapeo de la selección al nombre de la columna en el DataFrame
    columna_dinamica = COL_MOD_CONTRACTUAL if filtro_seleccionado == "Mod. Contractual" else filtro_seleccionado
    
    if columna_dinamica in df_filtered.columns:
        df_dinamico = df_filtered[columna_dinamica].value_counts().reset_index()
        df_dinamico.columns = [columna_dinamica, 'Cantidad']
        fig_pie_dinamico = px.pie(df_dinamico, values='Cantidad', names=columna_dinamica,
                                  color_discrete_sequence=['#4b8bbe', '#132c66', '#ed7d31'])
        fig_pie_dinamico.update_traces(textposition='outside', textinfo='percent')
        fig_pie_dinamico.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250)
        st.plotly_chart(fig_pie_dinamico, use_container_width=True)
    else:
        st.warning(f"La columna {columna_dinamica} no existe en la base de datos.")

st.markdown("---")

# 6. Tablas de Detalle
st.markdown("**Resumen por Tipo de Búsqueda y Objetivos**")
# Agrupación simulando la tabla intermedia
if COL_TIPO_BUSQUEDA in df_filtered.columns:
    df_resumen = df_filtered.groupby(COL_TIPO_BUSQUEDA).agg(
        Q_Busq=('N° Ticket', 'count'),
        Dias_Demora_Promedio=(COL_DIAS_DEMORA, 'mean')
    ).reset_index()
    # Formateo
    df_resumen['Dias_Demora_Promedio'] = df_resumen['Dias_Demora_Promedio'].round(0)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)

st.markdown("**Detalle Operativo de Búsquedas**")
# Aplicar color a la columna de demora para simular formato condicional
def color_demora(val):
    if isinstance(val, (int, float)):
        color = '#ffcccc' if val > 0 else '#ccffcc'
        return f'background-color: {color}'
    return ''

# Mostrar la tabla final
columnas_mostrar = [col for col in ["N° Ticket", COL_TIPO_BUSQUEDA, COL_EMPRESA, "Provincia", COL_ESTADO, COL_DIAS_DEMORA] if col in df_filtered.columns]
st.dataframe(df_filtered[columnas_mostrar].style.map(color_demora, subset=[COL_DIAS_DEMORA] if COL_DIAS_DEMORA in columnas_mostrar else []), 
             use_container_width=True, hide_index=True)

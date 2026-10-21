import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard de Selección | People Analytics", layout="wide")
st.title("📊 Dashboard Dinámico de Selección y Reclutamiento")

# 2. Carga de datos (Caché para optimizar rendimiento)
@st.cache_data(ttl=600) # Se actualiza cada 10 minutos
def load_data():
    # URL transformada a formato CSV para lectura directa
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS80spSAFpaYNM_WigjJoBXrpOdwVo9TpR1Eqf3Fyrjsa8IDHU1AJnmq2tvBCMgS4Daxb4vt3cIyKZ4/pub?output=csv"
    df = pd.read_csv(sheet_url)
    return df

df_original = load_data()

# 3. Diccionario de Criterios (SLA) basado en la imagen
# Asegúrate de que la columna en tu Google Sheet coincida con estos nombres de "Categoría"
criterios_sla = {
    "Posventa": {"sobresaliente": 15, "muy_bueno": 20, "regular": 25},
    "Chapa y pintura": {"sobresaliente": 25, "muy_bueno": 30, "regular": 40},
    "Administración concesionarios": {"sobresaliente": 15, "muy_bueno": 20, "regular": 25},
    "Staff (Analistas)": {"sobresaliente": 25, "muy_bueno": 30, "regular": 40},
    "Mandos medios": {"sobresaliente": 25, "muy_bueno": 30, "regular": 40},
    "Gerencias - Sub Gerencias": {"sobresaliente": 40, "muy_bueno": 50, "regular": 60},
    "Asesores comerciales- Adm come": {"sobresaliente": 15, "muy_bueno": 20, "regular": 25}
}

# 4. Función de Semaforización
def calcular_semaforo(row):
    # NOTA: Reemplaza 'Categoria' y 'Dias_Activos' por los nombres reales de tus columnas en el Sheet
    categoria = row.get('Categoria', '')
    dias = row.get('Dias_Activos', 0)
    
    if categoria in criterios_sla:
        limites = criterios_sla[categoria]
        if dias <= limites["sobresaliente"]:
            return "🟢 Sobresaliente"
        elif dias <= limites["muy_bueno"]:
            return "🟡 Muy Bueno"
        elif dias <= limites["regular"]:
            return "🟠 Regular"
        else:
            return "🔴 Crítico / Excedido"
    return "⚪ Sin métrica"

# Aplicar la semaforización al DataFrame
# st.write(df_original.columns) # Descomenta esto si necesitas ver los nombres exactos de tus columnas
if 'Categoria' in df_original.columns and 'Dias_Activos' in df_original.columns:
    df_original['Estado_SLA'] = df_original.apply(calcular_semaforo, axis=1)
else:
    st.warning("⚠️ Asegúrate de tener las columnas 'Categoria' y 'Dias_Activos' en tu Google Sheet para que el semáforo funcione correctamente. Puedes ajustar estos nombres en el código.")
    # Creando columnas dummy para que el dashboard no falle si los nombres no coinciden inicialmente
    df_original['Estado_SLA'] = "⚪ Sin métrica"

# 5. Barra lateral para Filtros dinámicos
st.sidebar.header("Filtros del Dashboard")
if 'Categoria' in df_original.columns:
    categorias_seleccionadas = st.sidebar.multiselect(
        "Filtrar por Categoría", 
        options=df_original['Categoria'].dropna().unique(),
        default=df_original['Categoria'].dropna().unique()
    )
    df_filtrado = df_original[df_original['Categoria'].isin(categorias_seleccionadas)]
else:
    df_filtrado = df_original

# 6. Métricas Clave (KPIs)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Búsquedas", len(df_filtrado))
with col2:
    if 'Dias_Activos' in df_filtrado.columns:
        promedio_dias = round(df_filtrado['Dias_Activos'].mean(), 1)
        st.metric("Tiempo Promedio (Días)", f"{promedio_dias}")
with col3:
    busquedas_en_sla = len(df_filtrado[df_filtrado['Estado_SLA'].isin(["🟢 Sobresaliente", "🟡 Muy Bueno"])])
    porcentaje_sla = round((busquedas_en_sla / len(df_filtrado)) * 100, 1) if len(df_filtrado) > 0 else 0
    st.metric("Cumplimiento SLA (%)", f"{porcentaje_sla}%")
with col4:
    busquedas_criticas = len(df_filtrado[df_filtrado['Estado_SLA'] == "🔴 Crítico / Excedido"])
    st.metric("Búsquedas Críticas", busquedas_criticas)

st.markdown("---")

# 7. Gráficos Interactivos
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Estado de Tiempos de Cobertura (SLA)")
    # Gráfico de torta para ver la distribución de los semáforos
    color_discrete_map = {
        "🟢 Sobresaliente": "#28a745", 
        "🟡 Muy Bueno": "#ffc107", 
        "🟠 Regular": "#fd7e14", 
        "🔴 Crítico / Excedido": "#dc3545",
        "⚪ Sin métrica": "#6c757d"
    }
    fig_pie = px.pie(
        df_filtrado, 
        names='Estado_SLA', 
        color='Estado_SLA',
        color_discrete_map=color_discrete_map,
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_graf2:
    if 'Categoria' in df_filtrado.columns and 'Dias_Activos' in df_filtrado.columns:
        st.subheader("Promedio de Días Activos por Categoría")
        df_agrupado = df_filtrado.groupby('Categoria')['Dias_Activos'].mean().reset_index()
        fig_bar = px.bar(
            df_agrupado, 
            x='Categoria', 
            y='Dias_Activos',
            text_auto='.1f',
            color='Dias_Activos',
            color_continuous_scale='Blues'
        )
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

# 8. Vista de Datos Detallada
st.subheader("Detalle de Búsquedas Activas")
# Mostramos la tabla con el semáforo como primera columna para rápida visualización
columnas_mostrar = ['Estado_SLA'] + [col for col in df_filtrado.columns if col != 'Estado_SLA']
st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)

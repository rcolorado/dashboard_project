# Description: Dashboard para visualizar métricas de recurrencia, conexiones, entrenamientos, datos del coach y cumplimentación de la plataforma bchange.
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
from io import BytesIO
from scripts.mongo_connector import get_company_names, get_groups_for_company
from scripts.data_processing import load_and_process_data, load_and_process_data_trainings, load_and_process_data_cumplimentacion
from scripts.metrics import calcular_metricas_recurrencia, calcular_metricas_connections, calcular_metricas_entrenamientos
from scripts.nlp_analysis import preprocess_text, plot_text_length_distribution, plot_word_frequency, sentiment_analysis, topic_modeling, generate_bigram_word_cloud, interpretar_sentimiento,  interpretar_subjetividad
from scripts.metrics import calcular_metricas_coach, contar_usuarios_unicos, obtener_resumen_progreso
from collections import Counter

# Colores personalizados
PRIMARY_COLOR = "#FF9E01"  # Naranja
TEXT_COLOR = "#00495E"  # Azul oscuro
ACCENT_COLOR = "#2A6A7D"  # Azul medio
BACKGROUND_COLOR = "#F8F9FA"  # Fondo claro


st.set_page_config(page_title="Dashboard bchange", 
                   page_icon="🚀", 
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={
                        'Get Help': 'https://www.extremelycoolapp.com/help',
                        'Report a bug': "https://www.extremelycoolapp.com/bug",
                        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

def check_password():
    st.markdown(
        f"""<h2 style='text-align: center; color: {TEXT_COLOR};'>Iniciar sesión</h2>""",
        unsafe_allow_html=True
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit_button = st.form_submit_button("Entrar")

        if submit_button:
            if username == st.secrets["app"]["APP_USERNAME"] and password ==  st.secrets["app"]["APP_PASSWORD"]:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")


# Autenticación
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.markdown(f"""<h1 style='text-align: center; color: {PRIMARY_COLOR}; font-size: 70px;'>Dashboard de bchange 👨‍🚀</h1>""",unsafe_allow_html=True)
    check_password()
    st.stop()
else:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""<h1 style='text-align: right; color: {PRIMARY_COLOR}; font-size: 30px;'>Dashboard de bchange 👨‍🚀</h1>""", unsafe_allow_html=True)

# Cargar el dataframe solo una vez por sesión
if "df" not in st.session_state:
    st.session_state.df = load_and_process_data()

df = st.session_state.df  # Referencia al dataframe en session_state

# Df entrenamientos, solo se carga una vez por sesión
if "df_trainings" not in st.session_state:
    st.session_state.df_trainings = load_and_process_data_trainings()
df_trainings = st.session_state.df_trainings  # Referencia al dataframe en session_state

# Df cumplimentación, solo una vez por sesión
if "df_cumplimentacion" not in st.session_state:
    st.session_state.df_cumplimentacion = load_and_process_data_cumplimentacion()

df_cumplimentacion = st.session_state.df_cumplimentacion  # Referencia al dataframe en session_state

# Estilos CSS personalizados
st.markdown(
    f"""
    <style>
        body {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
        }}
        .block-container {{
            padding-top: 1rem;
        }}
        .stDataFrame {{
            border-radius: 8px;
            border: 1px solid {ACCENT_COLOR};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Filtros
metric_type = st.selectbox("Seleccione el tipo de métrica", ["Recurrencia", "Conexiones", "Entrenamientos", "Coach", "Cumplimentación"], index=0)

if metric_type != "Entrenamientos":
   # Empresas excluidas
    empresas_excluidas = ["Auren", "Demos Clientes"]

# Obtener y filtrar empresas
    company_names = get_company_names()
    company_names = [name for name in company_names if name not in empresas_excluidas]

    selected_company = st.selectbox("Seleccione una empresa", ["Todas"] + company_names)

    # Obtener y filtrar grupos si se seleccionó una empresa
    if selected_company != "Todas":
        groups = get_groups_for_company(selected_company)
        groups = [g for g in groups if g != "Cumplimentación"]
    else:
        groups = []

    selected_group = st.selectbox("Seleccione un grupo", ["Todos"] + groups)
else:
    selected_company = None
    selected_group = None

if metric_type == "Recurrencia":
    st.markdown(f"<h2 style='color: {ACCENT_COLOR};'> \U0001F4CC Métricas de {metric_type}</h2>", unsafe_allow_html=True)
    
    company_filter = selected_company if selected_company != "Todas" else None
    group_filter = selected_group if selected_group != "Todos" else None
    
    df_metrics, df_additional = calcular_metricas_recurrencia(df, company_filter, group_filter)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("\U0001F465 Total de Usuarios", f"{int(df_metrics['Cantidad de Usuarios'].sum())}")
    with col2:
        valor = df_additional.loc['connection_count', 0]
        valor = 0 if pd.isna(valor) else int(valor)
        st.metric("⏳ Tiempo Medio de Conexión", f"{valor} sesiones")
    with col3:
        valor = df_additional.loc['days_since_completion', 0]
        valor = 0 if pd.isna(valor) else int(valor)
        st.metric("📅 Días desde Check-out", f"{valor} días")
    col4, col5 = st.columns(2)
    with col4:
        st.markdown("### 📊 Distribución de Usuarios")
        st.dataframe(df_metrics)
    with col5: 
       # Add written summary
        st.markdown(f"""
        <div style='background-color: {BACKGROUND_COLOR}; padding: 1rem; border-radius: 8px;'>
            <h3 style='color: {PRIMARY_COLOR};'>¿Qué significa estar en recurrencia?</h3>
            <ul style='color: {TEXT_COLOR};'>
                </p>Un usuario se encuentra en recurrencia si cumple <strong> tres condiciones</strong></p>
                <ul>
                    <li style='margin-left: 3rem;'>Ha terminado el programa (check-out completo).</li>
                    <li style='margin-left: 3rem;'>Ha vuelto a entrar a la plataforma, aunque sea al día siguiente de haber terminado el programa.</li>
                    <li style='margin-left: 3rem;'>Se ha conectado durante el año 2025.</li>
                </ul>
            </ul>
        </div>
        """, unsafe_allow_html=True) 
    
    fig = px.bar(df_metrics, x="Terminó el programa", y="Cantidad de Usuarios", color="Recurrencia", text="Porcentaje de Usuarios",
                 color_discrete_map={"SÍ": PRIMARY_COLOR, "NO": ACCENT_COLOR}, title="Distribución de Usuarios")
    fig.update_traces(texttemplate="%{text}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

elif metric_type == "Conexiones":
    st.markdown(f"<h2 style='color: {ACCENT_COLOR};'> \U0001F4CC Métricas de {metric_type}</h2>", unsafe_allow_html=True)
    
    company_filter = selected_company if selected_company != "Todas" else None
    group_filter = selected_group if selected_group != "Todos" else None
    
    df_connections = calcular_metricas_connections(df, company_filter, group_filter)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔢 Número total de conexiones", f"{int(df_connections['connection_id'].nunique())} conexiones")
    with col2:
        valor = df_connections['connectionDuration'].mean()
        valor = 0 if pd.isna(valor) else int(valor)
        st.metric("⏱ Tiempo de conexión medio/sesión", f"{valor} minutos")
    
    col3,col4 = st.columns(2)
    with col3:
        st.markdown("### 📊 Tiempo de conexión medio por compañía")
        df_show = df_connections.groupby("company_name", as_index=False).agg({"connectionDuration": "mean"}).sort_values(by="connectionDuration", ascending=False)
        df_show.rename(columns={"company_name": "Empresa", "connectionDuration": "Tiempo medio de conexión (minutos)"}, inplace=True)
        # Redondear a entero
        df_show["Tiempo medio de conexión (minutos)"] = df_show["Tiempo medio de conexión (minutos)"].round(0).astype(int)
        st.dataframe(df_show)
    
    with col4: 
        df_connections["startDate"] = pd.to_datetime(df_connections["startDate"])
        df_connections["day_of_week"] = df_connections["startDate"].dt.day_name()
        df_weekly = df_connections.groupby("day_of_week")["connectionDuration"].count().reset_index()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df_weekly["day_of_week"] = pd.Categorical(df_weekly["day_of_week"], categories=day_order, ordered=True)
        df_weekly = df_weekly.sort_values("day_of_week")
        fig = px.bar(df_weekly, x="day_of_week", y="connectionDuration", title="Conexiones acumuladas por día de la semana",
                     labels={"day_of_week": "Día de la semana", "connectionDuration": "Número de conexiones"},
                     color_discrete_sequence=["#1f77b4"])
        st.plotly_chart(fig, use_container_width=True)
    
    fig = px.bar(df_show, x="Empresa", y="Tiempo medio de conexión (minutos)", color="Empresa", text="Tiempo medio de conexión (minutos)",
                 title="Distribución de tiempo de conexión por compañía")
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

elif metric_type == "Coach":
    st.markdown(f"<h2 style='color: {ACCENT_COLOR};'> 👨‍🚀 Métricas de {metric_type}</h2>", unsafe_allow_html=True)

    company_filter = selected_company if selected_company != "Todas" else None
    group_filter = selected_group if selected_group != "Todos" else None
    
    respondieron_msg,  recibieron_msg_summary, respondieron_msg_summary = calcular_metricas_coach(df_trainings, company_filter, group_filter)
    total_recibieron = recibieron_msg_summary['# Usuarios'].sum()
    total_respondieron = respondieron_msg_summary['# Usuarios'].sum()
    usuarios = contar_usuarios_unicos(df_trainings, fecha_inicio='2025-02-28', company_name=company_filter, group_name = group_filter)

    # Diseño en columnas para las métricas
    st.markdown("### 👥 Distribución de Usuarios")
    st.metric (label="👤 Nº total de usuarios", value = f"{usuarios}", help = "Nº total de usuarios que han recibido el mensaje del coach")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(label="📩 Abrieron mensaje ", value=f"{total_recibieron}", help=" Nº total de usuarios que clickaron el pop-up del coach")

    with col2:
        st.metric(label="📨 Respondieron", value = f"{total_respondieron}", help = "Nº total de usuarios que respondieron el mensaje del coach")
        # Crear DataFrame para el gráfico de barras
        df_plot = pd.DataFrame({
            "Estado": ["Recibieron mensaje", "Respondieron mensaje"],
            "Cantidad de Usuarios": [total_recibieron, total_respondieron]
        })

    # Gráfico de barras: Recibieron vs. Respondieron
    st.markdown("### 📊 Comparación de Usuarios que Abrieron vs. Respondieron")
    fig = px.bar(df_plot, x="Estado", y="Cantidad de Usuarios", text="Cantidad de Usuarios",
                color="Estado", color_discrete_map={
                    "Abrieron mensaje": "#2A6A7D",  # Azul
                    "Respondieron mensaje": "#ff7f0e"  # Naranja
                },
                title="Usuarios que Abrieron vs. Respondieron el mensaje")

    fig.update_traces(texttemplate="%{text}", textposition="outside")
    fig.update_layout(yaxis_title="Cantidad de Usuarios")

    st.plotly_chart(fig, use_container_width=True)

    # Función para descargar el DataFrame en Excel
    def descargar_excel(df, nombre_archivo="datos_coach.xlsx"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Datos")
        output.seek(0)
        return output

    # Mostrar el DataFrame `respondieron_msg`
    st.markdown("### 📋 Detalle de las conversaciones")
    st.dataframe(respondieron_msg, use_container_width=True)

    # Botón para descargar los datos en Excel
    excel_file = descargar_excel(respondieron_msg)
    st.download_button(
        label="📥 Descargar datos en Excel",
        data=excel_file,
        file_name="conversaciones_coach.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif metric_type == "Cumplimentación":
    st.markdown(f"<h2 style='color: {ACCENT_COLOR};'> \U0001F4CC Métricas de {metric_type}</h2>", unsafe_allow_html=True)
    # Filtros
    company_filter = selected_company if selected_company != "Todas" else None
    group_filter = selected_group if selected_group != "Todos" else None
    # Checkbox para incluir usuarios sin progreso
    incluir_sin_progreso = st.checkbox("Incluir usuarios sin progreso", value=False,  help="Si se activa, se incluirán también los usuarios que no han completado ningún ejercicio."
)

    df_cumplimentacion, resumen_ejercicios = obtener_resumen_progreso(
        df_cumplimentacion,
        company_filter,
        group_filter,
        include_zero_progress=incluir_sin_progreso
    )
    # --- KPIs
    total_usuarios = df_cumplimentacion["user_id"].nunique()
    porcentaje_completado = df_cumplimentacion["progress_percent"].mean()
    st.markdown("##### 📊 Resumen de Cumplimentación General")

    kpi1, kpi2= st.columns(2)
    kpi1.metric("👤 Usuarios", total_usuarios)
    kpi2.metric("📈 % Cumplimentación media", f"{porcentaje_completado:.2f}%", help="Porcentaje de cumplimentación total teniendo en cuenta los tres módulos")

   
    # --- Resumen por módulo
    st.markdown("---")
    st.markdown("### 📚 Cumplimentación por módulo")
    resumen_modulos= df_cumplimentacion.groupby("module_name")["progress_percent"].mean().reset_index().sort_values(by="progress_percent", ascending=False)
    resumen_modulos= resumen_modulos.rename(columns={
    'module_name': 'Módulo',
    'progress_percent': 'Porcentaje (%)'
    })
    # Redondear a 2 decimales
    resumen_modulos['Porcentaje (%)'] = resumen_modulos['Porcentaje (%)'].round(2)
     # Reemplazar los valores en la columna 'Tipo'
    resumen_modulos['Módulo'] = resumen_modulos['Módulo'].replace({
        'transformacion-intrapersonal': 'Módulo 1: Transformación Intrapersonal',
        'transformacion-interpersonal': 'Módulo 2: Transformación Interpersonal',  
        'transformacion-transversal': 'Módulo 3: Transformación Transversal',
    })
    col3, col4 = st.columns(2)
    with col3:
        st.dataframe(resumen_modulos, use_container_width=True)

    # Crear el gráfico de barras
    with col4:
        fig_modulos = px.bar(
            resumen_modulos.sort_values("Porcentaje (%)", ascending=True),
            x="Porcentaje (%)",
            y="Módulo",
            orientation="h",
            color="Porcentaje (%)",
            color_continuous_scale=[[0, ACCENT_COLOR], [1, PRIMARY_COLOR]],
            labels={"Porcentaje (%)": "% Completado", "Módulo": "Módulo"},
            title="Progreso por módulo (%)",
            text="Porcentaje (%)"  # Añadir el porcentaje como texto en cada barra
        )
        fig_modulos.update_layout(
            yaxis_title="", 
            xaxis_title="% Completado", 
            height=400,
            font_color=TEXT_COLOR,
            plot_bgcolor=BACKGROUND_COLOR,
            paper_bgcolor=BACKGROUND_COLOR
        )

        # Hacer que las etiquetas (porcentaje) se ajusten mejor sobre las barras
        fig_modulos.update_traces(texttemplate='%{text}%', textposition='outside')

        # Mostrar el gráfico
        st.plotly_chart(fig_modulos, use_container_width=True)
  
    # Filtrar por módulo
    modulo_1 = resumen_ejercicios[resumen_ejercicios["module_name"] == "transformacion-intrapersonal"]
    modulo_2 = resumen_ejercicios[resumen_ejercicios["module_name"] == "transformacion-interpersonal"]
    modulo_3 = resumen_ejercicios[resumen_ejercicios["module_name"] == "transformacion-transversal"]
    modulo_1_clean = modulo_1.reset_index(drop=True)
    modulo_2_clean = modulo_2.reset_index(drop=True)
    modulo_3_clean = modulo_3.reset_index(drop=True)

    # Función para preparar cada dataframe
    def preparar_dataframe(df, total_usuarios):
        # Añadir la columna de porcentaje de completado
        df["Porcentaje completado"] = ((df["completed_count"] / total_usuarios) * 100).round(2)

        # Renombrar columnas
        df = df[["exercise_name_complete", "completed_count", "Porcentaje completado"]].copy()
        df.columns = ["Ejercicio", "Nº veces completado", "Porcentaje (%)"]
        
        # Ordenar por número de veces completado de mayor a menor
        return df.sort_values("Nº veces completado", ascending=False)

    # En tu código de Streamlit, usa la función como sigue
    col5, col6, col7 = st.columns(3)

    # Mostrar tablas con los datos de los módulos
    with col5:
        st.markdown("##### 🧠 Módulo 1: Transformación Intrapersonal")
        st.dataframe(preparar_dataframe(modulo_1_clean, total_usuarios), use_container_width=True)

    with col6:
        st.markdown("##### 🤝 Módulo 2: Transformación Interpersonal")
        st.dataframe(preparar_dataframe(modulo_2_clean, total_usuarios), use_container_width=True)

    with col7:
        st.markdown("##### 🔄 Módulo 3: Transformación Transversal")
        st.dataframe(preparar_dataframe(modulo_3_clean, total_usuarios), use_container_width=True)

    PRIMARY_COLOR_SOFT = "#FFD16C"  # Tono más claro de PRIMARY_COLOR
    ACCENT_COLOR_SOFT = "#A2BDC4"   # Tono más claro de ACCENT_COLOR

    def mostrar_podium(df, nombre_modulo):
        top = df.sort_values("completed_count", ascending=False).iloc[0]
        bottom = df.sort_values("completed_count", ascending=True).iloc[0]
        st.markdown(
            f"""
            <h4 style="text-align: center; margin-bottom: 35px;">{nombre_modulo}</h4>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
                <div style="background-color:{PRIMARY_COLOR_SOFT}; padding:10px; border-radius:9px; text-align:center; color:white; max-width: 550px; margin: auto; margin-bottom: 35px;">
                    <h4>🔥 Más completado</h4>
                    <h3>{top['exercise_name_complete']}</h3>
                    <p><b>{top['completed_count']} veces</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div style="background-color:{ACCENT_COLOR_SOFT}; padding:12px; border-radius:12px; text-align:center; color:{ACCENT_COLOR}; max-width: 550px; margin: auto;margin-bottom: 35px;">
                    <h4>❄️ Menos completado</h4>
                    <h3>{bottom['exercise_name_complete']}</h3>
                    <p><b>{bottom['completed_count']} veces</b></p>
                </div>
                """,
                unsafe_allow_html=True
            )
    st.markdown("------------------------------------------------------------------------------------------")
    st.markdown("#### 🔝 Ejercicios más y menos completados")
    # Mostrar "podiums"
    mostrar_podium(modulo_1, "1. Transformación Intrapersonal")
    mostrar_podium(modulo_2, "2. Transformación Interpersonal")
    mostrar_podium(modulo_3, "3. Transformación Transversal")

        #top_bottom_1(modulo_1, "🧠 Intrapersonal"),
        #top_bottom_1(modulo_2, "🤝 Interpersonal"),
        #top_bottom_1(modulo_3, "🔄 Transversal")
    st.markdown("------------------------------------------------------------------------------------------")
    # Botón para descargar los datos en Excel
    # Función para descargar el DataFrame en Excel
    def descargar_excel(df, nombre_archivo="datos_cumplimentacion.xlsx"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Datos")
        output.seek(0)
        return output
    excel_file = descargar_excel(df_cumplimentacion)
    st.download_button(
        label="📥 Descargar datos en Excel",
        data=excel_file,
        file_name="datos_cumplimentacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

elif metric_type == "Entrenamientos":
    st.markdown(f"<h2 style='color: {ACCENT_COLOR};'> \U0001F4CC Métricas de {metric_type}</h2>", unsafe_allow_html=True)
    df_trainings_summary, valid_training_actions, valid_training_notepad_one_note, valid_training_notepad_two_note, valid_training_affirmations, valid_survey_answers_suggestions, training_affirmations_summary = calcular_metricas_entrenamientos(df_trainings, None, None)
    
    # Add module name filter
    module_names = df_trainings_summary['Módulo'].unique()
    selected_module = st.selectbox("Seleccione un módulo", ["Todos"] + list(module_names))
    
    if selected_module != "Todos":
        df_trainings_summary = df_trainings_summary[df_trainings_summary['Módulo'] == selected_module]
    
    # Display the dataframe with filtering capabilities
    st.dataframe(df_trainings_summary, use_container_width=True)
    
    # Function to convert multiple dataframes to Excel and return as bytes
    def to_excel(dfs, sheet_names):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for df, sheet_name in zip(dfs, sheet_names):
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        processed_data = output.getvalue()
        return processed_data

    # Reset index for dataframes with MultiIndex and flatten columns
    def reset_and_flatten(df):
        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(map(str, col)).strip() for col in df.columns.values]
        return df

    valid_training_actions = reset_and_flatten(valid_training_actions)
    valid_survey_answers_suggestions = reset_and_flatten(valid_survey_answers_suggestions)
    valid_training_notepad_one_note = reset_and_flatten(valid_training_notepad_one_note)
    valid_training_notepad_two_note = reset_and_flatten(valid_training_notepad_two_note)
    training_affirmations_summary = reset_and_flatten(training_affirmations_summary)
    valid_training_affirmations = reset_and_flatten(valid_training_affirmations)

    # Combine all dataframes into one Excel file with multiple sheets
    dfs = [
        valid_training_actions,
        valid_survey_answers_suggestions,
        valid_training_notepad_one_note,
        valid_training_notepad_two_note,
        training_affirmations_summary,
        valid_training_affirmations
    ]
    sheet_names = [
        "Y ahora qué",
        "Sugerencias",
        "Cuaderno de 1 hoja",
        "Cuaderno de 2 hojas",
        "¡Sigue tus avances!",
        "Otras cosas"
    ]

    # Add download button
    st.download_button(
        label="📥 Descargar campos de texto abierto en Excel",
        data=to_excel(dfs, sheet_names),
        file_name="Campos_de_texto_abierto.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Add some space before the written summary
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Calculate metrics for the summary
    total_users = df_trainings_summary['Disponible (#)'].sum()
    avg_users_per_training = df_trainings_summary['Completado (#)'].mean()
    completion_rate = (df_trainings_summary['Completado (#)'].sum() / total_users) * 100
    claro_rate = df_trainings_summary['Claro (%)'].mean()
    util_rate = df_trainings_summary['Útil (%)'].mean()
    suggestions_rate = df_trainings_summary['Sugerencias (%)'].mean()
    other_things_rate = df_trainings_summary['Otras cosas que te llevas del entrenamiento (%)'].mean()
    # Convertir la columna a numérico, forzando los valores no convertibles a NaN
    df_trainings_summary['¿Y ahora qué? (%)'] = pd.to_numeric(df_trainings_summary['¿Y ahora qué? (%)'], errors='coerce')
    # Calcular la media, ignorando los NaN
    open_text_rate = df_trainings_summary['¿Y ahora qué? (%)'].mean()
    df_trainings_summary['Cuaderno (%)'] = pd.to_numeric(df_trainings_summary['Cuaderno (%)'], errors='coerce')
    notebook_rate = df_trainings_summary['Cuaderno (%)'].mean()
    df_trainings_summary['Check (%)'] = pd.to_numeric(df_trainings_summary['Check (%)'], errors='coerce')
    checklist_rate = df_trainings_summary['Check (%)'].mean()
    other_comments_rate = df_trainings_summary['Otras cosas que te llevas del entrenamiento (%)'].mean()
    
    # Add written summary
    st.markdown(f"""
    <div style='background-color: {BACKGROUND_COLOR}; padding: 1rem; border-radius: 8px;'>
        <h3 style='color: {PRIMARY_COLOR};'>Resumen de métricas de entrenamientos</h3>
        <ul style='color: {TEXT_COLOR};'>
            <li>Cada entrenamiento fue completado por alrededor de <strong>{avg_users_per_training:.0f}</strong> usuarios</li>
            <li>Las siguientes métricas son porcentajes relativos a la cantidad de usuarios que completaron entrenamientos:</li>
            <ul>
                <li style='margin-left: 3rem;'><strong>Claros</strong>: {claro_rate:.0f}%</li>
                <li style='margin-left: 3rem;'><strong>Útiles</strong>: {util_rate:.0f}%</li>
            </ul>
            <li>En la sección de <strong>Sugerencias</strong>, un <strong>{suggestions_rate:.0f}%</strong> de los usuarios dejaron comentarios.</li>
            <li>Alrededor del <strong>{checklist_rate:.0f}%</strong> de usuarios utilizan la checklist al final de los entrenamientos y alrededor del <strong>{other_comments_rate:.0f}%</strong> dejaron comentarios en Otras cosas que te llevas del entrenamiento.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

# NLP Analysis

    with st.expander("💬 Análisis NLP de Sugerencias"):

        # Example usage with valid_training_actions
        valid_survey_answers_suggestions['Sugerencias'].fillna("", inplace=True)

        valid_survey_answers_suggestions['processed_sugerencias'] = valid_survey_answers_suggestions['Sugerencias'].apply(preprocess_text)
        valid_survey_answers_suggestions['processed_sugerencias'] = valid_survey_answers_suggestions['processed_sugerencias'].apply(lambda x: x.replace(' él ', ' '))
        all_actions_text = ' '.join(valid_survey_answers_suggestions['processed_sugerencias'])

        st.markdown(f"<h2 style='color: {TEXT_COLOR};'> 💬 Análisis de Sugerencias </h2>", unsafe_allow_html=True)
        # Calculate mean length of suggestions
        # Calcular métricas
        total_sugerencias = valid_survey_answers_suggestions.shape[0]  # Número total de sugerencias
        mean_length = valid_survey_answers_suggestions['processed_sugerencias'].apply(len).mean()  # Media de longitud (en caracteres)

        # Diseño en columnas
        col1, col2 = st.columns(2)

        with col1:
            st.metric("💬 Nº total de Sugerencias", f"{total_sugerencias} sugerencias")

        with col2:
            st.metric("📏 Longitud media de las Sugerencias", f"{mean_length:.0f} caracteres")
        # Plot text length distribution
        fig = plot_text_length_distribution(valid_survey_answers_suggestions, 'Sugerencias', 'Distribución de la longitud de las Sugerencias', PRIMARY_COLOR, TEXT_COLOR)
        st.plotly_chart(fig, use_container_width=True)

        # Plot word frequency
        fig = plot_word_frequency(all_actions_text, 'Top 20 Palabras Más Frecuentes en las Sugerencias', PRIMARY_COLOR, TEXT_COLOR)
        st.plotly_chart(fig, use_container_width=True)

        # Sentiment analysis
        sentiment = sentiment_analysis(all_actions_text)
        # Interpretar resultados
        interpretacion_sentimiento = interpretar_sentimiento(sentiment.polarity)
        interpretacion_subjetividad = interpretar_subjetividad(sentiment.subjectivity)

        # Mostrar resultados en el dashboard
        st.markdown("## 📊 Análisis de Sentimientos")

        # Mostrar en columnas para un diseño más claro
        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="📈 Polaridad", value=f"{sentiment.polarity:.2f}", help="Indica si el sentimiento es positivo (cercano a 1), negativo (cercano a -1) o neutro (cercano a 0).")
            st.markdown(f"**{interpretacion_sentimiento}**")

        with col2:
            st.metric(label="🧠 Subjetividad", value=f"{sentiment.subjectivity:.2f}", help="Muestra si el texto es objetivo (cercano a 0) o subjetivo (cercano a 1).")
            st.markdown(f"**{interpretacion_subjetividad}**")

        # Texto explicativo adicional para mayor claridad
        st.info("""
        ✅ **Cómo interpretar los resultados:**
        - **Polaridad**: Evalúa el sentimiento del texto:
            - Valores positivos indican **sentimientos positivos**.
            - Valores negativos indican **sentimientos negativos**.
            - Valores cercanos a 0 indican un **sentimiento neutro**.
        - **Subjetividad**: Evalúa el grado de opinión:
            - Valores cercanos a 0 indican **objetividad**.
            - Valores cercanos a 1 indican **subjetividad**.
        """)
        # Sección: Análisis de Tópicos
        st.markdown("## 🔍  Análisis de Tópicos")
        st.info("""
        ✅ **¿Qué es el Análisis de Tópicos?**
        Identifica los principales temas mencionados en las sugerencias, lo que ayuda a comprender las áreas de interés o preocupación.
        """)
        st.markdown("#### Tópicos Identificados:")
        topics = topic_modeling(all_actions_text, n_topics=3, n_words=5)

        # Mostrar los tópicos en la interfaz de Streamlit
        for i, topic in enumerate(topics, start=1):
            st.markdown(f"**Tópico {i}:** {topic}")


        # Sección: Nube de Palabras (Bigramas)
        st.markdown("## ☁️ Bigram Word Cloud")
        st.info("""
        ✅ **¿Qué es un Bigrama?**
        Es una combinación de dos palabras que aparecen juntas con frecuencia. Esto ayuda a identificar patrones y temas clave en las respuestas.
        """)

        # Generar Word Cloud optimizado
        buf = generate_bigram_word_cloud(
            all_actions_text,
            title='Bigram Word Cloud de las Sugerencias',
            text_color=TEXT_COLOR,
            max_words=70,          # Limitar la cantidad de palabras
            background_color="white",  # Fondo blanco para mayor claridad
            colormap="cividis"      # Mejor paleta de colores
        )
        # Mostrar el gráfico en Streamlit
        st.image(buf)
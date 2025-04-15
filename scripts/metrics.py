import pandas as pd

def calcular_metricas_recurrencia(df, company_name=None, group_name=None):
    # Unir datos de usuarios, grupos y empresas
    df_recurrencia = df["users"].merge(df["groups"], how="left").merge(df["companies"], how="left")
    
    # Aplicar filtros si se especifican
    if company_name:
        df_recurrencia = df_recurrencia[df_recurrencia["company_name"] == company_name]
    if group_name:
        df_recurrencia = df_recurrencia[df_recurrencia["group_name"] == group_name]
    
    # Filtrar por tipo de progreso específico
    df_progress = df["progress"].query("progress_type == 'progress_checkpoint'")
    
    # Agregar cantidad de checkpoints y última fecha
    df_progress_recurrencia = df_progress.groupby("user_id").agg(
        checkpoint_count=("progress_type", "size"),
        checkpoint_date=("completionDate", "max")
    ).reset_index()
    
    df_connections_recurrencia = df["connections"].merge(df_progress_recurrencia, how="left")
    
    # Obtener la última fecha de conexión por usuario
    df_connections_recurrencia = df_connections_recurrencia.groupby("user_id")["endDate"].max().reset_index().merge(
        df_connections_recurrencia.query("endDate > checkpoint_date").groupby("user_id").agg(
            connection_count=("user_id", "size")
        ).reset_index(), how="left"
    )
    
    # Fusionar datos
    df_recurrencia = df_recurrencia.merge(df_progress_recurrencia, how="left").merge(df_connections_recurrencia, how="left")
    
    # Calcular diferencia de días entre checkpoint y última conexión
    df_recurrencia["checkpoint_date"] = pd.to_datetime(df_recurrencia["checkpoint_date"])
    df_recurrencia["endDate"] = pd.to_datetime(df_recurrencia["endDate"])
    df_recurrencia["days_since_completion"] = (df_recurrencia["endDate"] - df_recurrencia["checkpoint_date"]).dt.days
    
    # Generar banderas (flags)
    df_recurrencia.eval("is_gerente = group_name.str.contains('Gerente')", inplace=True)
    df_recurrencia.eval("is_active_2025 = endDate > '2024-12-31'", inplace=True)
    df_recurrencia.eval("is_finished = checkpoint_count > 1", inplace=True)
    df_recurrencia.eval("is_recurrent_2025 = is_active_2025 and is_finished and (days_since_completion > 0)", inplace=True)
    df_recurrencia.eval("is_recurrent = is_finished and (days_since_completion > 0)", inplace=True)
    
    # Calcular métricas
    metrics = df_recurrencia.groupby(["is_finished", "is_recurrent_2025"]).size().reset_index().rename(columns={0: "count"})
    metrics.eval("percentage = (count / count.sum()) * 100", inplace=True)
    
    metrics.replace({False: "NO", True: "SÍ"}, inplace=True)
    metrics["percentage"] = metrics["percentage"].round(1).astype(str) + "%"
    metrics.rename(
        columns={
            "is_finished": "Terminó el programa",
            "is_recurrent_2025": "Recurrencia",
            "count": "Cantidad de Usuarios",
            "percentage": "Porcentaje de Usuarios",
        }, inplace=True
    )
    
    # Promedio de conexiones y días desde la finalización
    promedios = df_recurrencia.query("is_recurrent_2025")[["connection_count", "days_since_completion"]].mean().to_frame().round(0)
    
    return metrics, promedios

def calcular_metricas_connections(df, company_name=None, group_name=None):
    df_connections = df["connections"].merge(df["users"], how="left", on="user_id").merge(
        df["groups"], how="left"
    ).merge(
        df["companies"], how="left"
    )
  # Verificar el resultado del merge
  # print("Después de merge de conexiones y usuarios:")
  # print(df_connections.head())

    # Aplicar filtros si se especifican
    if company_name:
        df_connections = df_connections[df_connections["company_name"] == company_name]
    if group_name:
        df_connections = df_connections[df_connections["group_name"] == group_name]

    # Unir ejercicios con respuestas
    df["exercises"] = df["exercises"].merge(df["answers"], how="left")

    # Explode listas module_id
    if "module_id" in df["exercises"].columns:
        df["exercises"] = df["exercises"].explode("module_id")

    # Unir ejercicios con módulos
    df["exercises"] = df["exercises"].merge(df["modules"], how="left")

    # Explode listas episode_id
    if "episode_id" in df["exercises"].columns:
        df["exercises"] = df["exercises"].explode("episode_id")
    df["exercises"] = df["exercises"].merge(df["episodes"], how="left")
    
    # Unir conexiones con ejercicios
    df_connections = df_connections.merge(df["exercises"], how="left")
    
    # Seleccionar columnas específicas y guardarlas en un nuevo DataFrame
    selected_columns = ["user_id", "connection_id", "connectionDuration", "group_name", "company_name",  "module_name", "episode_name", "exercise_name", "startDate"]
    df_selected = df_connections[selected_columns]

    return df_selected

def calcular_metricas_entrenamientos(df, module_name=None, company_name=None, group_name=None):
    df_companies = df["companies"][["_id", "name"]].rename(columns={"_id": "company", "name": "company_name"})
    df_groups = df["groups"][["_id", "name", "company"]].rename(columns={"_id": "group", "name": "group_name"})
    df_users = df["users"][[
        '_id', 'company', 'group'
    ]].rename(columns={"_id": "user"}).merge(df_groups).merge(df_companies)

    df_trainings = pd.json_normalize(df["trainings"][[
        'namedId',
        'steps', 'elements', 'ideas', 'actions', 'questionnaire', 'survey',
        'translations',
    ]].explode('steps').explode('elements').explode('ideas').explode("actions").to_dict(orient="records"))
    df_trainings = pd.json_normalize(
        df_trainings.explode("questionnaire.affirmations").to_dict(orient="records")
    )
    df_translations = pd.json_normalize(df["translations"].to_dict(orient="records"))
    training_meta = pd.DataFrame({
        'valor-ser-curioso': [1, 1, "El valor de ser curioso"],
        'mis-monstruos': [1, 2, "Mis monstruos"],
        'flexibilidad-consciente': [1, 3, "Flexibilidad consciente"],
        'aprender-confiar': [2, 4, "Aprender a confiar"],
        'empatia-ceguera-emocional': [2, 5, "Empatía y ceguera emocional"],
        'circulos-influencia': [2, 6, "Círculos de influencia"],
        'modelo-grow-mando': [3, 7, "Modelo GROW"],
        'construyendo-puentes': [3, 8, "Construyendo puentes"],
        'ayudas-colaboras': [3, 9, "¿Ayudas o colaboras?"],
        "total": [None, None, "Total"]
    }, index=["Módulo", "Orden Entrenamiento", "Entrenamiento"]).T.reset_index().rename(columns={
        "index": "trainingNamedId",
        0: "Módulo",
        1: "Orden Entrenamiento",
        2: "Entrenamiento"
    })
    df_progress_complete = df["progress"].query("type == 'progress_training' and completed").trainingNamedId.value_counts().to_frame()
    df_progress_complete = df_progress_complete.reset_index().rename(columns={
        "count": "Completado (#)"
    })
    df_progress_available = df["progress"].query("type == 'progress_training'").trainingNamedId.value_counts().to_frame()
    df_progress_available = df_progress_available.reset_index().rename(columns={
        "count": "Disponible (#)"
    })
    df_progress = df_progress_complete.merge(df_progress_available, on="trainingNamedId", how="left")
    df_progress["Completado (%)"] = (100 * df_progress["Completado (#)"] / df_progress["Disponible (#)"]).round().astype(int)
    df_progress_summary = training_meta.merge(df_progress).drop(columns=["trainingNamedId"])

    survey_questions_translations_title_oid = [str(x["translations"]["title"]) for x in df["surveys"]["questions"][0]]
    survey_questions_oid_translations_title_oid = {str(x["_id"]): str(x["translations"]["title"]) for x in df["surveys"]["questions"][0]}
    df_translations_survey_questions = df["translations"].astype({"_id": str}).query("_id in @survey_questions_translations_title_oid").copy()
    df_translations_survey_questions["content"] = df_translations_survey_questions["content"].apply(lambda x: x["es"])
    translation_oid_title_survey_questions = df_translations_survey_questions.set_index("_id")["content"].to_dict()
    oid_title_survey_questions = {question: translation_oid_title_survey_questions[trans] for question, trans in survey_questions_oid_translations_title_oid.items()}
    survey_answers = pd.json_normalize(
        df["answers"].query("type == 'answer_survey_training'")[["user", "trainingNamedId", "items"]].explode("items").to_dict(orient="records")
    )
    survey_answers.columns = survey_answers.columns.str.replace("items.", "")
    survey_answers["question"] = survey_answers["question"].astype(str).map(oid_title_survey_questions)
    survey_answers_summary = survey_answers.drop(columns=["user"]).query("type != 'input'").fillna("NS/NC").groupby(["trainingNamedId", "question"]).value_counts().to_frame().reset_index()[["trainingNamedId", "question", "value", "count"]]
    survey_answers_summary["value"] = survey_answers_summary["value"].map({
        True: "Sí",
        False: "No",
        "NS/NC": "NS/NC"
    })
    survey_answers_summary = survey_answers_summary.sort_values(["trainingNamedId", "question", "value"], ascending=[True, True, False])
    survey_answers_summary.rename(columns={
        "question": "Pregunta", "value": "Respuesta",
    }, inplace=True)
    survey_answers_summary = survey_answers_summary.query(
        "Respuesta == 'Sí'"
    ).pivot(
        columns=["Pregunta", "Respuesta"],
        index=["trainingNamedId"],
        values="count"
    ).droplevel(1, axis=1).reset_index().rename(columns={
        "¿Te ha resultado claro?": "Claro (#)",
        "¿Te ha sido útil el contenido de este entrenamiento?": "Útil (#)"
    })
    survey_answers_summary = training_meta.merge(survey_answers_summary).merge(df_progress)
    survey_answers_summary["Claro (%)"] = (100 * survey_answers_summary["Claro (#)"] / survey_answers_summary["Completado (#)"]).round().astype(int)
    survey_answers_summary["Útil (%)"] = (100 * survey_answers_summary["Útil (#)"] / survey_answers_summary["Completado (#)"]).round().astype(int)
    survey_answers_summary = survey_answers_summary.drop(columns=[
        "trainingNamedId", "Completado (#)", "Disponible (#)", "Completado (%)", "Claro (#)", "Útil (#)"
])  
    question = "¿Cambiarías alguna cosa del entrenamiento?"
    survey_answers_suggestions = survey_answers.query("question == @question")[["user", "trainingNamedId", "input"]]
    survey_answers_suggestions["input"] = survey_answers_suggestions["input"].astype(str).apply(lambda x: None if len(x) <= 7 else x)
    valid_survey_answers_suggestions_summary = survey_answers_suggestions.groupby("trainingNamedId")["input"].apply(lambda x: x.notna().sum()).to_frame().reset_index()
    valid_survey_answers_suggestions_summary = training_meta.merge(valid_survey_answers_suggestions_summary).merge(df_progress)
    valid_survey_answers_suggestions_summary["input"] = valid_survey_answers_suggestions_summary["input"].fillna(0).astype(int)
    valid_survey_answers_suggestions_summary["Sugerencias (%)"] = (100 * valid_survey_answers_suggestions_summary["input"] / valid_survey_answers_suggestions_summary["Completado (#)"]).round().astype(int)
    valid_survey_answers_suggestions_summary = valid_survey_answers_suggestions_summary.drop(columns=[
        "trainingNamedId", "Completado (#)", "Disponible (#)", "Completado (%)", "input"
    ])
    survey_answers_summary = survey_answers_summary.merge(valid_survey_answers_suggestions_summary)
    valid_survey_answers_suggestions = survey_answers_suggestions.dropna().rename(columns={
        "input": "Sugerencias"
    })
    valid_survey_answers_suggestions = df_users.merge(training_meta.merge(valid_survey_answers_suggestions)).drop(columns=[
        "trainingNamedId", "company", "group"
    ]).rename(columns={
        "user": "Usuario", "group_name": "Grupo", "company_name": "Empresa"
    })
    type = "answer_training_action"
    training_actions = df["answers"].query("type == @type")[[
        "user", 'trainingNamedId', 'action', 'input',
    ]]
    training_actions = training_actions.merge(
        df_trainings[[
        "actions._id", "actions.translations.name",
    ]].drop_duplicates().merge(
        df_translations[[
            "_id", "content.es"
        ]], left_on="actions.translations.name", right_on="_id", how="left"
    ), left_on="action", right_on="actions._id", how="left"
    )
    training_actions = training_actions.drop(columns=["action", "_id", "actions._id", "actions.translations.name"])
    training_actions.rename(columns={"content.es": "action"}, inplace=True)
    training_actions["input"] = training_actions["input"].astype(str)
    training_actions["input"] = training_actions["input"].apply(lambda x: None if len(x) <= 7 else x)
    valid_training_actions_summary = training_actions.groupby(["user", "trainingNamedId"])["input"].apply(
        lambda x: x.notna().mean()
    ).groupby(
        "trainingNamedId"
    ).sum().to_frame().reset_index()
    valid_training_actions_summary = training_meta.merge(valid_training_actions_summary).merge(df_progress)
    valid_training_actions_summary["input"] = valid_training_actions_summary["input"].fillna(0).astype(int)
    valid_training_actions_summary["¿Y ahora qué? (%)"] = (100 * valid_training_actions_summary["input"] / valid_training_actions_summary["Completado (#)"]).round().astype(int)
    valid_training_actions_summary = valid_training_actions_summary.drop(columns=[
        "trainingNamedId", "Completado (#)", "Disponible (#)", "Completado (%)", "input"
    ])
    valid_training_actions = training_actions.dropna().rename(columns={
    "action": "¿Y ahora qué?", "input": "Respuesta"
})[[
    "user", "trainingNamedId", "¿Y ahora qué?", "Respuesta"
]]
    valid_training_actions = df_users.merge(training_meta.merge(valid_training_actions)).drop(columns=[
        "trainingNamedId", "company", "group"
    ]).rename(columns={
        "user": "Usuario", "group_name": "Grupo", "company_name": "Empresa"
    })
    valid_training_actions = pd.pivot_table(
        valid_training_actions.sort_values(["Orden Entrenamiento", "Usuario", "Empresa", "Grupo"]),
        index=["Usuario", "Empresa", "Grupo"],
        columns=["Módulo", "Orden Entrenamiento", "Entrenamiento", "¿Y ahora qué?"],
        values="Respuesta",
        aggfunc="first",
        sort=False
    )
    valid_training_actions = valid_training_actions.drop(columns=valid_training_actions.columns[[7, 10]])
    type = "answer_training_notepad"
    training_notepad = df["answers"].query("type == @type")[[
        "user", 'trainingNamedId', 'notepad', 'firstNoteInput', 'secondNoteInput',
    ]]
    training_notepad = training_notepad.merge(
        df_trainings[[
        "elements._id", "elements.translations.title", "elements.firstNote.translations.name", 'elements.secondNote.translations.name',
    ]].drop_duplicates().merge(
        df_translations[[
            "_id", "content.es"
        ]], left_on="elements.translations.title", right_on="_id", how="left"
    ), left_on="notepad", right_on="elements._id", how="left"
    ).drop(columns=["_id"]).rename(columns={
        "content.es": "title"
    }).merge(
        df_translations[[
            "_id", "content.es"
        ]], left_on="elements.firstNote.translations.name", right_on="_id", how="left"
    ).drop(columns=["_id"]).rename(columns={
        "content.es": "firstNote"
    }).merge(
        df_translations[[
            "_id", "content.es"
        ]], left_on="elements.secondNote.translations.name", right_on="_id", how="left"
    ).drop(columns=["_id"]).rename(columns={
        "content.es": "secondNote"
    }).drop(columns=[
        "notepad", "elements._id", "elements.translations.title", "elements.firstNote.translations.name", 'elements.secondNote.translations.name'
    ])

    training_notepad_one_note = training_notepad.query(
        "firstNote != firstNote and secondNote != secondNote"
    ).drop(columns=["firstNote", "secondNote", "secondNoteInput"])
    training_notepad_one_note

    valid_training_notepad_one_note_summary = training_notepad_one_note.copy()
    valid_training_notepad_one_note_summary["firstNoteInput"] = training_notepad_one_note["firstNoteInput"].apply(lambda x: None if len(x) <= 7 else x)
    valid_training_notepad_one_note_summary = valid_training_notepad_one_note_summary.groupby(["user", "trainingNamedId"])["firstNoteInput"].apply(
        lambda x: x.notna().mean()
    ).groupby(
        "trainingNamedId"
    ).sum().to_frame().reset_index()
    valid_training_notepad_one_note_summary = training_meta.merge(valid_training_notepad_one_note_summary).merge(df_progress)
    valid_training_notepad_one_note_summary["firstNoteInput"] = valid_training_notepad_one_note_summary["firstNoteInput"].fillna(0).astype(int)
    valid_training_notepad_one_note_summary["firstNoteInput"] = (100 * (valid_training_notepad_one_note_summary["firstNoteInput"] / valid_training_notepad_one_note_summary["Completado (#)"])).round().astype(int)
    valid_training_notepad_one_note_summary = valid_training_notepad_one_note_summary.drop(columns=[
        "trainingNamedId", "Completado (#)", "Disponible (#)", "Completado (%)"
    ]).rename(columns={
        "firstNoteInput": "Cuaderno (%)"
    })
    valid_training_notepad_one_note = training_notepad_one_note.dropna().rename(columns={
        "title": "Cuaderno", "firstNoteInput": "Respuesta"  
    })[["user", "trainingNamedId", "Cuaderno", "Respuesta"]]
    valid_training_notepad_one_note = df_users.merge(valid_training_notepad_one_note).merge(training_meta).drop(columns=[
        "trainingNamedId", "company", "group"
    ]).rename(columns={
        "user": "Usuario", "group_name": "Grupo", "company_name": "Empresa"
    })
    valid_training_notepad_one_note = pd.pivot_table(
        valid_training_notepad_one_note.sort_values(["Orden Entrenamiento", "Usuario", "Empresa", "Grupo"]),
        index=["Usuario", "Empresa", "Grupo"],
        columns=["Módulo", "Orden Entrenamiento", "Entrenamiento", "Cuaderno"],
        values="Respuesta",
        aggfunc="first",
        sort=False
    )
    training_notepad_two_note = training_notepad.query(
    "firstNote == firstNote and secondNote == secondNote"
)

    valid_training_notepad_two_note_summary = training_notepad_two_note.copy()
    valid_training_notepad_two_note_summary["firstNoteInput"] = training_notepad_two_note["firstNoteInput"].apply(lambda x: None if x and len(x) <= 7 else x)
    valid_training_notepad_two_note_summary = valid_training_notepad_two_note_summary.groupby(["user", "trainingNamedId"])["firstNoteInput"].apply(
        lambda x: x.notna().mean()
    ).groupby(
        "trainingNamedId"
    ).sum().to_frame().reset_index()
    valid_training_notepad_two_note_summary = training_meta.merge(valid_training_notepad_two_note_summary).merge(df_progress)
    valid_training_notepad_two_note_summary["firstNoteInput"] = valid_training_notepad_two_note_summary["firstNoteInput"].fillna(0).astype(int)
    valid_training_notepad_two_note_summary["firstNoteInput"] = (100 * (valid_training_notepad_two_note_summary["firstNoteInput"] / valid_training_notepad_two_note_summary["Completado (#)"])).round().astype(int)
    valid_training_notepad_two_note_summary = valid_training_notepad_two_note_summary.drop(columns=[
            "trainingNamedId", "Completado (#)", "Disponible (#)", "Completado (%)"
        ]).rename(columns={
            "firstNoteInput": "Cuaderno (%)"
        })
    valid_training_notepad_summary = pd.concat([valid_training_notepad_one_note_summary, valid_training_notepad_two_note_summary])
    valid_training_notepad_summary = valid_training_notepad_summary.sort_values("Orden Entrenamiento").groupby([
            "Módulo", "Orden Entrenamiento", "Entrenamiento"
        ]).mean().reset_index()
    valid_training_notepad_summary["Cuaderno (%)"] = valid_training_notepad_summary["Cuaderno (%)"].round().astype(int)
    valid_training_notepad_two_note = training_notepad_two_note.dropna().rename(columns={
    "title": "Cuaderno Título",
    "firstNote": "Cuaderno 1", "secondNote": "Cuaderno 2",
    "firstNoteInput": "Respuesta 1", "secondNoteInput": "Respuesta 2"
    })[["user", "trainingNamedId", "Cuaderno Título", "Cuaderno 1", "Respuesta 1", "Cuaderno 2", "Respuesta 2"]]
    valid_training_notepad_two_note = df_users.merge(valid_training_notepad_two_note).merge(training_meta).drop(columns=[
        "trainingNamedId", "company", "group"
    ]).rename(columns={
        "user": "Usuario", "group_name": "Grupo", "company_name": "Empresa"
    })
    valid_training_notepad_two_note = pd.pivot_table(
        valid_training_notepad_two_note.drop(columns=[
            "Cuaderno 2", "Respuesta 2"
        ]).sort_values(["Orden Entrenamiento", "Usuario", "Empresa", "Grupo"]),
        index=["Usuario", "Empresa", "Grupo"],
        columns=["Módulo", "Orden Entrenamiento", "Entrenamiento", "Cuaderno Título", "Cuaderno 1"],
        values="Respuesta 1",
        aggfunc="first",
        sort=False
    ).merge(
        pd.pivot_table(
            valid_training_notepad_two_note.drop(columns=[
                "Cuaderno 1", "Respuesta 1"
            ]).sort_values(["Orden Entrenamiento", "Usuario", "Empresa", "Grupo"]),
            index=["Usuario", "Empresa", "Grupo"],
            columns=["Módulo", "Orden Entrenamiento", "Entrenamiento", "Cuaderno Título", "Cuaderno 2"],
            values="Respuesta 2",
            aggfunc="first",
            sort=False
        ), left_index=True, right_index=True
    )
    # Sort columns MultiIndex by level 1 and 0
    valid_training_notepad_two_note = valid_training_notepad_two_note.reindex(
        sorted(valid_training_notepad_two_note.columns, key=lambda x: (x[1], x[0])),
        axis=1
    )
    type = "answer_training_questionnaire"
    training_affirmations = pd.json_normalize(df["answers"].query("type == @type")[[
        "user", 'trainingNamedId', 'endingAffirmationInput', 'items',
    ]].explode("items").to_dict(orient="records"))
    training_affirmations = training_affirmations.merge(
            df_trainings[[
            "questionnaire.affirmations._id", "questionnaire.affirmations.translations.name"
        ]].drop_duplicates().merge(
            df_translations[[
                "_id", "content.es"
            ]], left_on="questionnaire.affirmations.translations.name", right_on="_id", how="left"
        ), left_on="items.affirmation", right_on="questionnaire.affirmations._id", how="left"
    )

    training_affirmations_summary = training_affirmations.query(
        "`items.isChecked` == True"
    ).copy()
    training_affirmations_summary = training_affirmations_summary.groupby(["content.es", "trainingNamedId"])["items.isChecked"].sum().to_frame().reset_index()
    training_affirmations_summary = training_meta.merge(training_affirmations_summary).merge(df_progress)
    training_affirmations_summary["items.isChecked"] = (100 * (training_affirmations_summary["items.isChecked"] / training_affirmations_summary["Completado (#)"])).round().astype(int)
    training_affirmations_summary = training_affirmations_summary.drop(columns=[
        "trainingNamedId", "Completado (#)", "Disponible (#)", "Completado (%)"
    ]).rename(columns={
        "content.es": "¡Sigue tus avances!", "items.isChecked": "Check (%)"
    })
    training_affirmations_summary_check = training_affirmations_summary.groupby([
    "Módulo", "Orden Entrenamiento", "Entrenamiento"
    ])["Check (%)"].mean().round().astype(int).reset_index()

    valid_training_affirmations = training_affirmations[["user", "trainingNamedId", "endingAffirmationInput"]].drop_duplicates()
    valid_training_affirmations_summary = valid_training_affirmations.copy()
    valid_training_affirmations_summary["endingAffirmationInput"] = valid_training_affirmations_summary["endingAffirmationInput"].astype(str).apply(lambda x: None if len(x) <= 7 else x)
    valid_training_affirmations_summary = valid_training_affirmations_summary.groupby(["user", "trainingNamedId"])["endingAffirmationInput"].apply(
        lambda x: x.notna().mean()
    ).groupby(
        "trainingNamedId"
    ).sum().to_frame().reset_index()
    valid_training_affirmations_summary = training_meta.merge(valid_training_affirmations_summary).merge(df_progress)
    valid_training_affirmations_summary["endingAffirmationInput"] = valid_training_affirmations_summary["endingAffirmationInput"].fillna(0).astype(int)
    valid_training_affirmations_summary["endingAffirmationInput"] = (100 * (valid_training_affirmations_summary["endingAffirmationInput"] / valid_training_affirmations_summary["Completado (#)"])).round().astype(int)
    valid_training_affirmations_summary = valid_training_affirmations_summary.drop(columns=[
        "trainingNamedId", "Completado (#)", "Disponible (#)", "Completado (%)"
    ]).rename(columns={
        "endingAffirmationInput": "Otras cosas que te llevas del entrenamiento (%)"
    })
    ignore_named_ids = ["modelo-grow"]
    valid_training_affirmations_summary = valid_training_affirmations_summary.query("Entrenamiento not in @ignore_named_ids")
    valid_training_affirmations = valid_training_affirmations.dropna().rename(columns={
    "endingAffirmationInput": "Otras cosas que te llevas del entrenamiento"
    })[["user", "trainingNamedId", "Otras cosas que te llevas del entrenamiento"]]
    ignore_named_ids = ["modelo-grow"]
    valid_training_affirmations = valid_training_affirmations.query("trainingNamedId not in @ignore_named_ids")
    valid_training_affirmations = df_users.merge(valid_training_affirmations).merge(training_meta).drop(columns=[
        "trainingNamedId", "company", "group"
    ]).rename(columns={
        "user": "Usuario", "group_name": "Grupo", "company_name": "Empresa"
    })
    valid_training_affirmations = pd.pivot_table(
        valid_training_affirmations.sort_values(["Orden Entrenamiento", "Usuario", "Empresa", "Grupo"]),
        index=["Usuario", "Empresa", "Grupo"],
        columns=["Módulo", "Orden Entrenamiento", "Entrenamiento"],
        values="Otras cosas que te llevas del entrenamiento",
        aggfunc="first",
        sort=False
    )
    df_trainings_summary = df_progress_summary.merge(
    survey_answers_summary,
    how="left"
).merge(
    valid_training_actions_summary,
    how="left"
).merge(
    valid_training_notepad_summary,
    how="left"
).merge(
    training_affirmations_summary_check,
    how="left"
).merge(
    valid_training_affirmations_summary,
    how="left"
)
    df_trainings_summary["¿Y ahora qué? (%)"] = df_trainings_summary["¿Y ahora qué? (%)"].astype("Int64").astype(str)
    df_trainings_summary["Cuaderno (%)"] = df_trainings_summary["Cuaderno (%)"].astype("Int64").astype(str)
    df_trainings_summary = df_trainings_summary.replace("<NA>", "")
    # Aplicar filtros si se especifican
    if module_name:
        df_trainings_summary = df_trainings_summary[df_progress_summary["Módulo"] == module_name]
    return df_trainings_summary, valid_training_actions, valid_training_notepad_one_note, valid_training_notepad_two_note, valid_training_affirmations, valid_survey_answers_suggestions, training_affirmations_summary

def calcular_metricas_coach(df, company_name = None, group_name = None):
    
    df_companies = df["companies"][["_id", "name"]].rename(columns={"_id": "company", "name": "company_name"})
    df_groups = df["groups"][["_id", "name", "company"]].rename(columns={"_id": "group", "name": "group_name"})
    df_users = df["users"][[
        '_id', "email", "firstName", "lastName", 'company', 'group'
    ]].rename(columns={"_id": "user"}).merge(df_groups).merge(df_companies)

    df_users["name"] = df_users["firstName"] + " " + df_users["lastName"]
    df_users.drop(columns=["firstName", "lastName"], inplace=True)
    df_coach = df["threads"].merge(df_users)
    ignore_companies = ["Demos Clientes"]
    df_coach = df_coach.query(
        "company_name not in @ignore_companies"
    ).reset_index(drop=True)

    # Normalizar DataFrame y valores de entrada
    df_coach["company_name"] = df_coach["company_name"].str.strip()
    df_coach["group_name"] = df_coach["group_name"].str.strip()

    company_name = company_name.strip() if company_name else None
    group_name = group_name.strip() if group_name else None

    # Aplicar los filtros
    if company_name and company_name != "todas":
        df_coach = df_coach[df_coach["company_name"] == company_name]

    if group_name and group_name != "todos":
        df_coach = df_coach[df_coach["group_name"] == group_name]

    # Tabla de usuarios que recibieron mensajes del coach: Empresa, Grupo, Usuario (nº de usuarios)
    recibieron_msg_summary = df_coach.query("assistantMessagesAmount > 0").groupby(["company_name", "group_name"]).size().to_frame("user_count").reset_index()
    recibieron_msg_summary = recibieron_msg_summary.rename(columns={
        "company_name": "Compañía", "group_name": "Grupo", "user_count": "# Usuarios"
    })
    recibieron_msg_summary.to_excel("Alcanzados por el coach.xlsx")
  
    respondieron_msg_summary = df_coach.query("userMessagesAmount > 0").groupby(["company_name", "group_name"]).size().to_frame("user_count").reset_index()
    respondieron_msg_summary = respondieron_msg_summary.rename(columns={
        "company_name": "Compañía", "group_name": "Grupo", "user_count": "# Usuarios"
    })
    respondieron_msg_summary.to_excel("Respondieron al coach.xlsx")
   
    # Tabla de usuarios que respondieron mensajes del coach
    respondieron_msg = pd.json_normalize(
    df_coach.query("userMessagesAmount > 0").explode("messages").to_dict(orient="records")
)
    respondieron_msg = respondieron_msg[[
        "company_name", "group_name", "name", "email", "messages.date", "messages.role", "messages.content"
    ]]
    respondieron_msg["messages.role"] = respondieron_msg["messages.role"].replace({
        "user": "Usuario", "assistant": "Coach"
    })
    respondieron_msg["messages.date"] = pd.to_datetime(respondieron_msg["messages.date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    respondieron_msg = respondieron_msg.rename(columns={
        "company_name": "Compañía", "group_name": "Grupo", "name": "Nombre", "email": "Correo",
        "messages.date": "Fecha", "messages.role": "Rol", "messages.content": "Mensaje"
    })
    # respondieron_msg.to_excel("Conversaciones coach.xlsx")
    return respondieron_msg,  recibieron_msg_summary,  respondieron_msg_summary

def contar_usuarios_antigua(df, fecha_inicio='2025-02-28', company=None, group=None):

    # Filtrar por fecha y usuarios que desbloquearon el coach
    df_filtrado = df.query("hasUnlockedCoach == True and startDate > @fecha_inicio")

    # Filtro opcional por empresa
    if company:
        df_filtrado = df_filtrado[df_filtrado["company_name"] == company]

    # Filtro opcional por grupo
    if group:
        df_filtrado = df_filtrado[df_filtrado["group_name"] == group]

    # Contar usuarios únicos
    return df_filtrado["user"].nunique()

def contar_usuarios_unicos(df, fecha_inicio='2025-02-28',  company_name = None, group_name = None):
    df_companies = df["companies"][["_id", "name"]].rename(columns={"_id": "company", "name": "company_name"})
    df_groups = df["groups"][["_id", "name", "company"]].rename(columns={"_id": "group", "name": "group_name"})
    df_users = df["users"][[
        '_id', "email", "firstName", "lastName", 'company', 'group', 'hasUnlockedCoach'
    ]].rename(columns={"_id": "user"}).merge(df_groups).merge(df_companies)
    df_users["name"] = df_users["firstName"] + " " + df_users["lastName"]
    df_users.drop(columns=["firstName", "lastName"], inplace=True)
    df_filtrado = df_users.merge(df["connections"], on="user", how="left")
        # Normalizar DataFrame y valores de entrada
    df_filtrado["company_name"] = df_filtrado["company_name"].str.strip()
    df_filtrado["group_name"] = df_filtrado["group_name"].str.strip()

    company_name = company_name.strip() if company_name else None
    group_name = group_name.strip() if group_name else None

    # Aplicar los filtros
    if company_name and company_name != "todas":
        df_filtrado= df_filtrado[df_filtrado["company_name"] == company_name]

    if group_name and group_name != "todos":
        df_filtrado= df_filtrado[df_filtrado["group_name"] == group_name]
    # Filtrar por fecha y usuarios que desbloquearon el coach
    df_filtrado = df_filtrado.query("hasUnlockedCoach == True and startDate > @fecha_inicio")

    # Contar usuarios únicos
    return df_filtrado["user"].nunique()

def obtener_resumen_progreso(df, company_name=None, group_name=None):
    # --- MERGE DE TODOS LOS DATAFRAMES ---
    # Merge df["progress"] with df["users"]
    df_progress_users = df["progress"].merge(df["users"], left_on="user_id", right_on="user_id", how="left")
    # Merge the result with df["modules"]
    df_progress_modules = df_progress_users.merge(df["modules"], left_on="module_id", right_on="module_id", how="left")
    # Merge the result with df["companies"]
    df_progress_modules_users_companies = df_progress_modules.merge(df["companies"], left_on="company_id", right_on="company_id", how="left")
    # Merge the result with df["groups"]
    df_progress_modules_users_companies_groups = df_progress_modules_users_companies.merge(df["groups"], left_on="group_id", right_on="group_id", how="left")
    # Final merged DataFrame
    df_merged = df_progress_modules_users_companies_groups

    # --- FILTROS POR EMPRESA Y GRUPO ---
    # Aplicar filtros si se especifican
    if company_name:
        df_merged = df_merged[df_merged["company_name"] == company_name]
    if group_name:
        df_merged = df_merged[df_merged["group_name"] == group_name]

    # --- RESUMEN GENERAL POR TIPO DE PROGRESO ---
    resumen_general = (
        df_merged.drop_duplicates(subset=["user_id", "progress_type"])
        .groupby("progress_type")
        .agg(
            total_usuarios=('user_id', 'nunique'),
            usuarios_completados=('completed', lambda x: x.sum())
        )
        .reset_index()
    )
    resumen_general["porcentaje_completado"] = (
        resumen_general["usuarios_completados"] / resumen_general["total_usuarios"] * 100
    ).round(2)

    # --- RESUMEN POR MÓDULO ---
    df_modulos = df_merged[df_merged["progress_type"] == "progress_module"].copy()
    df_modulos = df_modulos.dropna(subset=["module_name"])
    df_modulos_unique = df_modulos.drop_duplicates(subset=["user_id", "module_name"])

    resumen_modulos = (
        df_modulos_unique.groupby("module_name")
        .agg(
            total_usuarios=('user_id', 'nunique'),
            usuarios_completados=('completed', lambda x: x.sum())
        )
        .reset_index()
    )
    resumen_modulos["porcentaje_completado"] = (
        resumen_modulos["usuarios_completados"] / resumen_modulos["total_usuarios"] * 100
    ).round(2)

    return df_merged, resumen_general, resumen_modulos

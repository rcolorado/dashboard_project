import pandas as pd
import streamlit as st
from scripts.mongo_connector import get_collection_data

# Definir colecciones necesarias
collection_names = ["companies", "groups", "users", "connections", "progress", "modules", "episodes", "exercises", "answers", "translations"
                    "surveys", "sessions", "trainings", "actions", "feedback"]

# Columnas a mantener y renombrar por colección
collection_columns = {
    "companies": {
        "keep": ["_id", "name"],
        "rename": {"_id": "company_id", "name": "company_name"}
    },
    "groups": {
        "keep": ["_id", "name"],
        "rename": {"_id": "group_id", "name": "group_name"}
    },
    "users": {
        "keep": ["_id", "group", "company", "email", "firstName", "lastName"],
        "rename": {"_id": "user_id", "group": "group_id", "company": "company_id", "email": "user_email", "firstName": "user_first_name", "lastName": "user_last_name"}
    },
    "connections": {
        "keep": ["_id", "user", "address", "endDate", "connectionDuration", "startDate"],
        "rename": {"_id": "connection_id", "user": "user_id"}
    },
    "progress": {
        "keep": ["_id", "user", "type", "completionDate", "createdAt", "updatedAt", "completed", "isViewed", "module"],
        "rename": {"_id": "progress_id", "user": "user_id", "type": "progress_type", "module": "module_id"}
    },
    "modules": {
        "keep": ["_id", "namedId"],
        "rename": {"_id": "module_id", "namedId": "module_name"}
    },
    "episodes": {
        "keep": ["_id", "namedId"],
        "rename": {"_id": "episode_id", "namedId": "episode_name"}
    },
    "exercises": {
        "keep": ["_id", "namedId", "modules", "episodes"],
        "rename": {"_id": "exercise_id", "namedId": "exercise_name", "modules": "module_id", "episodes": "episode_id"}
    },
    "answers": {
        "keep": ["_id", "exercise", "user"],
        "rename": {"_id": "answer_id", "exercise": "exercise_id", "user": "user_id"}
    },
    "translations": {
        "keep": ["_id", "namedId"],
        "rename": {"_id": "translation_id", "namedId": "translation_name"}
    }
}

@st.cache_data
def load_and_process_data():
    """Carga datos de MongoDB y los procesa en DataFrames, excluyendo empresas y grupos no deseados."""
    df = {col: get_collection_data(col) for col in collection_columns.keys()}

    for col, columns in collection_columns.items():
        if not df[col].empty:
            if "keep" in columns:
                df[col] = df[col][columns["keep"]]
            if "rename" in columns and columns["rename"]:
                df[col] = df[col].rename(columns=columns["rename"])

    # Filtrar empresas no deseadas
    empresas_excluidas = ["Auren", "Demos Clientes"]
    df["companies"] = df["companies"][~df["companies"]["company_name"].isin(empresas_excluidas)]

    # Conservar sólo grupos de empresas válidas
    empresas_validas_ids = df["companies"]["company_id"]
    if not df["users"].empty:
        df["users"] = df["users"][df["users"]["company_id"].isin(empresas_validas_ids)]

    if not df["groups"].empty:
        df["groups"] = df["groups"][
            df["groups"]["group_name"] != "Cumplimentación"
        ]
        grupos_validos_ids = df["groups"]["group_id"]
        if not df["users"].empty:
            df["users"] = df["users"][df["users"]["group_id"].isin(grupos_validos_ids)]

    return df

@st.cache_data
def load_and_process_data_trainings():
    """Carga datos de MongoDB y los procesa en DataFrames, excluyendo empresas y grupos no deseados."""
    collection_names = [
        "surveys", "connections", "progress", "companies", "groups", "answers",
        "sessions", "trainings", "actions", "feedback", "users", "translations",
        "threads"
    ]

    # Cargar datos
    df = {collection: get_collection_data(collection) for collection in collection_names}

    # Filtrar empresas no deseadas
    empresas_excluidas = ["Auren", "Demos Clientes"]
    if not df["companies"].empty:
        df["companies"] = df["companies"][~df["companies"]["name"].isin(empresas_excluidas)]

    # Filtrar usuarios por empresas válidas
    empresas_validas_ids = df["companies"]["_id"]
    if not df["users"].empty:
        df["users"] = df["users"][df["users"]["company"].isin(empresas_validas_ids)]

    # Filtrar grupos no deseados
    if not df["groups"].empty:
        df["groups"] = df["groups"][df["groups"]["name"] != "Cumplimentación"]
        grupos_validos_ids = df["groups"]["_id"]

        # Filtrar usuarios por grupos válidos
        if not df["users"].empty:
            df["users"] = df["users"][df["users"]["group"].isin(grupos_validos_ids)]

    return df

@st.cache_data
def load_and_process_data_cumplimentacion():
    """Carga datos de MongoDB y los procesa en DataFrames, excluyendo empresas y grupos no deseados."""
    df = {col: get_collection_data(col) for col in collection_columns.keys()}

    for col, columns in collection_columns.items():
        if not df[col].empty:
            if "keep" in columns:
                df[col] = df[col][columns["keep"]]
            if "rename" in columns and columns["rename"]:
                df[col] = df[col].rename(columns=columns["rename"])

    # Filtrar empresas no deseadas
    empresas_excluidas = ["Auren", "Demos Clientes"]
    df["companies"] = df["companies"][~df["companies"]["company_name"].isin(empresas_excluidas)]

    # Conservar sólo grupos de empresas válidas
    empresas_validas_ids = df["companies"]["company_id"]
    if not df["users"].empty:
        df["users"] = df["users"][df["users"]["company_id"].isin(empresas_validas_ids)]

    if not df["groups"].empty:
        df["groups"] = df["groups"][
            df["groups"]["group_name"] != "Cumplimentación"
        ]
        grupos_validos_ids = df["groups"]["group_id"]
        if not df["users"].empty:
            df["users"] = df["users"][df["users"]["group_id"].isin(grupos_validos_ids)]

    return df
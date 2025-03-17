import pandas as pd
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
        "keep": ["_id", "user", "type", "completionDate", "createdAt", "updatedAt", "completed", "isViewed"],
        "rename": {"_id": "progress_id", "user": "user_id", "type": "progress_type"}
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


def load_and_process_data():
    """Carga datos de MongoDB y los procesa en DataFrames."""
    df = {col: get_collection_data(col) for col in collection_columns.keys()}

    for col, columns in collection_columns.items():
        if not df[col].empty:
            if "keep" in columns:
                df[col] = df[col][columns["keep"]]
            if "rename" in columns and columns["rename"]:
                df[col] = df[col].rename(columns=columns["rename"])
                
    return df


def load_and_process_data_trainings():
    """Carga datos de MongoDB y los procesa en DataFrames."""
    collection_names = [
        "surveys", "connections", "progress", "companies", "groups", "answers",
        "sessions", "trainings", "actions", "feedback", "users", "translations",
        "threads"
    ]

    df = {
            collection: get_collection_data(collection) for collection in collection_names
        }
    return df

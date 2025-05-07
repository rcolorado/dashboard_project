import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
# load_dotenv()  # Cargar variables de entorno

# Conectar a MongoDB
MONGO_URI = st.secrets["mongodb"]["MONGO_URI"]
DB_NAME = st.secrets["mongodb"]["MONGO_DB"]

def get_mongo_connection():
    """Devuelve una conexión a la base de datos MongoDB."""
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def get_collection_data(collection_name):
    """Obtiene los datos de una colección en MongoDB y los convierte en un DataFrame."""
    db = get_mongo_connection()
    data = list(db[collection_name].find())
    return pd.DataFrame(data) if data else pd.DataFrame()

def get_company_names():
    """Obtiene la lista de nombres de empresas disponibles en la base de datos."""
    db = get_mongo_connection()
    companies = db["companies"].find({}, {"name": 1, "_id": 0})  
    return sorted([company["name"] for company in companies])  

def get_groups_for_company(company_name):
    """Obtiene la lista de nombres de grupos disponibles para la empresa seleccionada."""
    db = get_mongo_connection()
    
    # Realiza la agregación para unir 'groups' y 'companies'
    groups_cursor = db["groups"].aggregate([
        {
            "$lookup": {
                "from": "companies",  # Colección de empresas
                "localField": "company",  # Campo en 'groups' que hace referencia al '_id' de 'companies'
                "foreignField": "_id",  # Campo en 'companies' que se referencia desde 'groups'
                "as": "company_details"  # El resultado de la unión se guarda en 'company_details'
            }
        },
        {
            "$unwind": "$company_details"  # Despliega el resultado de la unión
        },
        {
            "$match": {  # Filtra los grupos que pertenecen a la empresa seleccionada
                "company_details.name": company_name
            }
        },
        {
            "$project": {  # Muestra solo el nombre de los grupos y elimina el _id
                "name": 1,  # Nombre del grupo
                "_id": 0  # Elimina el campo _id
            }
        }
    ])
    
    # Extrae los nombres de los grupos y los retorna ordenados
    groups_list = [group["name"] for group in groups_cursor]
    
    if not groups_list:
        print(f"No se encontraron grupos para la empresa {company_name}")
    
    return sorted(groups_list)    
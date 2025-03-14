# Usa una imagen base oficial de Python
FROM python:3.9-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos del proyecto al contenedor
COPY . /app

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Establece la variable de entorno para Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

# Expone el puerto 8501 para que Streamlit sea accesible
EXPOSE 8501

# Comando para ejecutar la aplicación de Streamlit
CMD ["streamlit", "run", "dashboard.py"]

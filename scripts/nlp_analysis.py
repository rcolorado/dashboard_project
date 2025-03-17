import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
from textblob import TextBlob
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import spacy
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
import subprocess

# Ensure you have the necessary NLTK data
nltk.download('stopwords')
nltk.download('punkt_tab')
# nltk.download('es_core_news_lg')
# Load the spaCy model

# Intentar cargar el modelo y descargarlo si no está disponible
try:
    nlp = spacy.load("es_core_news_md")
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", "es_core_news_md"])
    nlp = spacy.load("es_core_news_md")

print("Modelo cargado exitosamente.")

# Define the preprocess_text function
def preprocess_text(text):
    if isinstance(text, str):  # Asegurarse de que sea un texto
        # Convertir a minúsculas
        text = text.lower()

        # Eliminar caracteres especiales y puntuación
        text = ''.join([char for char in text if char not in string.punctuation])

        # Eliminar palabras problemáticas directamente antes de la tokenización
        for word in ['él', 'ella', 'ellos', 'ellas']:
            text = text.replace(f' {word} ', ' ')

        # Tokenización
        tokens = word_tokenize(text)

        # Eliminar stopwords en español y otras palabras irrelevantes
        stop_words = set(stopwords.words("spanish")).union({'él', 'ella', 'ellos', 'ellas', 'lo', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'de', 'en', 'por', 'para', 'y', 'que', 'con', 'a', 'al', 'del', 'se', 'es', 'la', 'las', 'lo', 'los'})
        tokens = [word for word in tokens if word not in stop_words]

        # Lematización con spaCy
        doc = nlp(' '.join(tokens))
        lemmatized_tokens = [token.lemma_ for token in doc]

        # Filtrar tokens lematizados que sean palabras de valor
        value_words = [word for word in lemmatized_tokens if len(word) > 2 and word not in stop_words]

        # Reemplazar manualmente cualquier 'él' que haya quedado después de la lematización
        value_words = [word for word in value_words if word != "él"]

        # Unir las palabras lematizadas en una sola cadena
        return ' '.join(value_words)
    return ""

# Function to plot the distribution of text length
def plot_text_length_distribution(data, column, title, primary_color, text_color):
    data[f'{column}_length'] = data[column].apply(len)
    fig = px.histogram(data, x=f'{column}_length', nbins=30, title=title, color_discrete_sequence=[primary_color])
    fig.update_layout(title_font_size=16, title_font_color=text_color, xaxis_title=f'Longitud de {column}', yaxis_title='Frecuencia')
    return fig

# Function to plot the top 20 most frequent words
def plot_word_frequency(data, title, primary_color, text_color):
    word_freq = Counter(data.split())
    most_common_words = word_freq.most_common(20)
    df_word_freq = pd.DataFrame(most_common_words, columns=['Palabra', 'Frecuencia'])

    # Ordenar de mayor a menor para que las más frecuentes aparezcan arriba
    df_word_freq = df_word_freq.sort_values(by='Frecuencia', ascending=True)

    fig = px.bar(df_word_freq, x='Frecuencia', y='Palabra', orientation='h', 
                 title=title, color_discrete_sequence=[primary_color])

    fig.update_layout(
        title_font_size=16,
        title_font_color=text_color,
        xaxis_title='Frecuencia',
        yaxis_title='Palabra',
        yaxis=dict(automargin=True, tickmode='array', tickvals=list(df_word_freq['Palabra'])),
    )

    # Ajustar el tamaño de la fuente de las etiquetas en el eje Y
    fig.update_yaxes(tickfont=dict(size=12))

    return fig

# Function to perform sentiment analysis
def sentiment_analysis(data):
    sentiment = TextBlob(data).sentiment
    return sentiment
# Función para interpretar el sentimiento
def interpretar_sentimiento(polarity):
    if polarity > 0.3:
        return "😊 Sentimiento Positivo"
    elif polarity < -0.3:
        return "😔 Sentimiento Negativo"
    else:
        return "😐 Sentimiento Neutro"

# Función para interpretar la subjetividad
def interpretar_subjetividad(subjectivity):
    if subjectivity >= 0.5:
        return "🔎 Texto Subjetivo"
    else:
        return "📊 Texto Objetivo"

# Función para limpiar el texto
def limpiar_texto(texto):
    # Normalizar acentos
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    # Eliminar caracteres especiales y números
    texto = re.sub(r'[^a-zA-Z\s]', '', texto)
    # Convertir a minúsculas
    texto = texto.lower()
    return texto

# Function to perform topic modeling
# Modelo LDA optimizado con tópicos únicos
def topic_modeling(data, n_topics=5, n_words=8):
    # Limpiar el texto
    textos_limpios = [limpiar_texto(doc) for doc in data.split('.')]
    
    # Vectorización de los textos
    vectorizer = CountVectorizer(stop_words=stopwords.words('spanish'))
    X = vectorizer.fit_transform(textos_limpios)
    
    # Crear el modelo LDA
    lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
    lda.fit(X)
    
    # Obtener los términos por tópico
    topics = lda.components_
    topic_terms = []
    
    for i, topic in enumerate(topics):
        terms = [vectorizer.get_feature_names_out()[index] for index in topic.argsort()[-n_words:]]
        topic_terms.append(' '.join(terms))
    
    # Mostrar solo los tópicos únicos (eliminamos duplicados)
    unique_topics = list(set(topic_terms))
    
    return unique_topics

# Function to generate a bigram word cloud
def generate_bigram_word_cloud(data, title, text_color, max_words=100, background_color='white', colormap='Blues'):
    # Vectorización del bigrama
    bigram_vectorizer = CountVectorizer(ngram_range=(2, 2), stop_words=stopwords.words('spanish'))
    X_bigram = bigram_vectorizer.fit_transform([data])
    
    # Obtener frecuencia de los bigramas
    bigrams_freq = dict(zip(bigram_vectorizer.get_feature_names_out(), X_bigram.toarray().sum(axis=0)))
    
    # Generar la nube de palabras
    wordcloud = WordCloud(width=800, height=400, background_color=background_color, colormap=colormap, max_words=max_words).generate_from_frequencies(bigrams_freq)
    
    # Mostrar la imagen
    plt.figure(figsize=(10, 6))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.title(title, fontsize=16, color=text_color)
    plt.axis('off')
    plt.tight_layout()
    
    # Guardar la imagen en memoria
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return buf

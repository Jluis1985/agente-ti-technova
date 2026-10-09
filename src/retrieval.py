import os
import sys
import warnings

# Ocultar todas las advertencias de deprecación de la consola
warnings.filterwarnings("ignore")

from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# Configuración de la base vectorial Chroma DB
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")

def obtener_vectorstore():
    embeddings = FastEmbedEmbeddings()
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )
    return vectorstore

def buscar_evidencia(query: str, k: int = 5):
    vectorstore = obtener_vectorstore()
    
    # Si la consulta es muy corta y contiene palabras clave, expandimos la búsqueda para Chroma DB
    query_busqueda = query
    query_lower = query.lower()
    if len(query.split()) <= 3 and any(w in query_lower for w in ["bloqueado", "bloqueo", "usuario", "cuenta"]):
        query_busqueda = f"{query} bloqueo de cuenta contraseña active directory"

    resultados = vectorstore.similarity_search(query_busqueda, k=k)
    return resultados

def formatear_contexto(docs):
    contexto_texto = ""
    for doc in docs:
        fuente = doc.metadata.get("source", "Documento Oficial")
        contexto_texto += f"\n--- Extraído de: {fuente} ---\n{doc.page_content}\n"
    return contexto_texto
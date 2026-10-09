import warnings
warnings.filterwarnings("ignore")import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.embeddings import FastEmbedEmbeddings
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma

load_dotenv()

# Ajuste automático para encontrar siempre la carpeta 'vectorstore' en la raíz
BASE_DIR = Path(__file__).resolve().parent.parent
VECTORSTORE_PATH = str(BASE_DIR / "vectorstore")

def buscar_evidencia(query: str, k: int = 3):
    """Busca los fragmentos más relevantes en ChromaDB."""
    embeddings = FastEmbedEmbeddings()
    vectorstore = Chroma(
        persist_directory=VECTORSTORE_PATH, 
        embedding_function=embeddings
    )
    
    results = vectorstore.similarity_search_with_relevance_scores(query, k=k)
    
    evidencias = []
    for doc, score in results:
        fuente = os.path.basename(doc.metadata.get("source", "Desconocido"))
        evidencias.append({
            "contenido": doc.page_content,
            "fuente": fuente,
            "score": round(score, 3)
        })
            
    return evidencias

def formatear_contexto(evidencias: list) -> str:
    """Formatea las evidencias encontradas con citas visibles."""
    if not evidencias:
        return "NO_EVIDENCIA"
    
    contexto = "EVIDENCIA RECUPERADA DE LAS POLÍTICAS:\n\n"
    for i, ev in enumerate(evidencias, 1):
        contexto += f"[Cita {i} - Fuente: {ev['fuente']}]\n"
        contexto += f"{ev['contenido']}\n\n"
        
    return contexto
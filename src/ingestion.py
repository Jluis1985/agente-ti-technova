import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

DATA_PATH = Path("data")
VECTORSTORE_PATH = "vectorstore"
MODEL_PATH = "./model_cache"

def load_documents():
    """Carga todos los documentos de la carpeta data/."""
    documents = []

    docx_loader = DirectoryLoader(
        path=str(DATA_PATH),
        glob="**/*.docx",
        loader_cls=Docx2txtLoader,
        show_progress=True
    )
    documents.extend(docx_loader.load())

    for ext in ["**/*.md", "**/*.txt"]:
        try:
            text_loader = DirectoryLoader(
                path=str(DATA_PATH),
                glob=ext,
                loader_cls=TextLoader,
                show_progress=True
            )
            documents.extend(text_loader.load())
        except Exception:
            pass

    print(f"\n✅ Se cargaron {len(documents)} documentos")
    return documents

def split_documents(documents):
    """Divide los documentos en fragmentos (chunks)."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Se crearon {len(chunks)} fragmentos (chunks)")
    return chunks

def create_vectorstore(chunks):
    """Crea la base vectorial con Chroma leyendo el modelo local."""
    print("\n🔄 Generando embeddings...")

    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_PATH,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTORSTORE_PATH
    )

    print(f"✅ Base vectorial creada y guardada en: {VECTORSTORE_PATH}")
    return vectorstore

def main():
    print("=== Iniciando ingestión de documentos ===\n")

    documents = load_documents()
    if not documents:
        print("❌ No se encontraron documentos en la carpeta data/")
        return

    chunks = split_documents(documents)
    create_vectorstore(chunks)

    print("\n🎉 ¡Ingestión completada con éxito!")

if __name__ == "__main__":
    main()

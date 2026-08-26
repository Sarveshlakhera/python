import os
import time
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import (
    PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredMarkdownLoader, CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_classic.indexes import SQLRecordManager, index

load_dotenv()

# Map file extensions to their respective LangChain Loaders
LOADER_MAPPING = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".md": UnstructuredMarkdownLoader,
    ".csv": CSVLoader,
}

def load_documents(data_dir: str):
    """Recursively load all supported documents from the data directory."""
    docs = []
    for filepath in Path(data_dir).rglob("*.*"):
        ext = filepath.suffix.lower()
        if ext in LOADER_MAPPING:
            try:
                loader = LOADER_MAPPING[ext](str(filepath))
                loaded_docs = loader.load()
                
                # Enhance metadata for citation tracking
                for doc in loaded_docs:
                    doc.metadata["timestamp"] = time.time()
                    doc.metadata["source_file"] = filepath.name
                
                docs.extend(loaded_docs)
            except Exception as e:
                print(f"Error loading {filepath.name}: {e}")
    return docs

def build_index():
    data_dir = os.getenv("DATA_DIR", "./data/input_docs")
    db_dir = os.getenv("CHROMA_PERSIST_DIR", "./db/chroma")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(db_dir, exist_ok=True)
    
    print(f"Loading documents from '{data_dir}'...")
    raw_docs = load_documents(data_dir)
    
    if not raw_docs:
        print("No documents found to process. Add files to the input directory.")
        return

    # Semantic/Recursive Chunking (~800 tokens, 100 overlap)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    docs = splitter.split_documents(raw_docs)
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
     
    vectorstore = Chroma(
        collection_name="rag_collection",
        embedding_function=embeddings,
        persist_directory=db_dir
    )
    
    # Initialize SQL Record Manager to track file checksums
    record_manager = SQLRecordManager(
        "chroma/rag_collection", db_url=f"sqlite:///{db_dir}/record_manager.sql"
    )
    record_manager.create_schema()
    
    print("Hashing files and incrementally synchronizing vector store...")
    
    # 'cleanup="incremental"' skips unchanged files, updates modified ones, 
    # and drops deleted ones based on the 'source' metadata key.
    result = index(
        docs,
        record_manager,
        vectorstore,
        cleanup="incremental",
        source_id_key="source" 
    )
    print(f"Indexing complete! Summary: {result}")

if __name__ == "__main__":
    build_index()